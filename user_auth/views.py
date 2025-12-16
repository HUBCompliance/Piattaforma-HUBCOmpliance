# Nel tuo file /user_auth/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib.auth import (
    login, authenticate, logout, update_session_auth_hash, get_user_model
) 
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm 
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView,
    # Importiamo con alias per chiarezza
    PasswordResetView as DjangoPasswordResetView,
    PasswordResetDoneView as DjangoPasswordResetDoneView,
    PasswordResetConfirmView as DjangoPasswordResetConfirmView,
    PasswordResetCompleteView as DjangoPasswordResetCompleteView,
)
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.views.decorators.http import require_POST
from django.db import IntegrityError
from django.db.models import Count, Q 
from django.http import HttpResponse, JsonResponse 
from django.contrib import messages 
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse_lazy
from django.utils.http import urlsafe_base64_encode
from django.core.exceptions import ObjectDoesNotExist
import requests # Richiesto per le chiamate API
import os


import openpyxl 
from openpyxl.styles import Font, Alignment, PatternFill 
from datetime import date 
from django.views.generic import View 

# Importazioni locali
from .forms import (
    LoginForm, RegisterForm, CustomPasswordResetForm, CustomSetPasswordForm,
    ReferenteUpdateForm, ConsulenteUpdateForm, ProfiloStudenteForm, AziendaProfileForm, SecurityLoginForm
)
from .models import CustomUser as User, Azienda, Consulente, NotaAzienda
# Importazioni da altre app
from courses.models import ImpostazioniSito
from compliance.models import CategoriaDocumento, DocumentoAziendale, VersioneDocumento 


# ==============================================================================
# FUNZIONE DEFINITIVA PER L'INVIO EMAILJS (Recupera i dati da ImpostazioniSito)
# ==============================================================================

def send_email_via_emailjs(payload):
    """
    Invia il payload JSON all'API di EmailJS utilizzando le chiavi salvate nel DB.
    """
    
    # 1. Recupera le chiavi dinamiche dal modello ImpostazioniSito
    try:
        config = ImpostazioniSito.objects.get(pk=1)
        
        # === ATTENZIONE: NOMI CAMPO DA VERIFICARE ===
        # Questi nomi devono corrispondere ai campi definiti nel modello ImpostazioniSito.
        service_id = getattr(config, 'emailjs_service_id', None)
        template_id = getattr(config, 'emailjs_reset_template_id', None) 
        user_id = getattr(config, 'emailjs_public_key', None) # La Public Key è l'User ID per l'API
        
        # Verifica che tutti i dati essenziali siano presenti
        if not all([service_id, template_id, user_id]):
            print("ERRORE: Credenziali EmailJS mancanti o incomplete in ImpostazioniSito.")
            return False
            
    except ObjectDoesNotExist:
        print("ERRORE: Modello ImpostazioniSito non trovato (necessario per EmailJS).")
        return False
    
    # 2. Configurazione dell'API
    API_URL = "https://api.emailjs.com/api/v1.0/email/send" 
    
    # 3. Costruzione del corpo della richiesta API
    data = {
        'service_id': service_id,
        'template_id': template_id,
        'user_id': user_id,
        'template_params': payload # Il nostro payload con reset_link, username, etc.
    }
    
    # 4. Chiamata API
    try:
        # Usa un timeout per non bloccare la richiesta
        response = requests.post(API_URL, json=data, timeout=10) 
        response.raise_for_status() # Solleva un'eccezione se il codice è 4xx o 5xx
        
        print(f"DEBUG EMAILJS: Invio riuscito. Status: {response.status_code}")
        return True # Invio OK
        
    except requests.exceptions.RequestException as e:
        print(f"ERRORE RICHIESTA EMAILJS: La chiamata API è fallita: {e}")
        return False # Invio Fallito


# ==============================================================================
# FUNZIONI AIUTO E CHECK (Helper Functions)
# ==============================================================================

def is_admin(user):
    """Verifica se l'utente è un superuser (admin)."""
    return user.is_authenticated and user.is_superuser

def is_studente(user): 
    return user.is_authenticated and user.ruolo == 'STUDENTE' and not user.is_staff

def is_profilo_user(user): 
    """Verifica se l'utente è un ruolo gestito (Studente, Referente, Consulente)."""
    if not user.is_authenticated or user.is_staff: return False
    return user.ruolo in ['STUDENTE', 'REFERENTE', 'CONSULENTE']

def trigger_set_password_email(request, user):
    """Simula l'invio dell'email per l'impostazione della password iniziale."""
    # PLACEHOLDER: Inserisci qui la tua logica di invio email
    pass 


# ==============================================================================
# 1. VISTE AUTENTICAZIONE E CUSTOM VIEW CLASSES
# ==============================================================================

def login_view(request):
    """Vista per la gestione del login (basata su funzione)"""
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('/') 
    else:
        form = LoginForm()
        
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('/login/') 

def register_view(request):
    # PLACEHOLDER: Logica di registrazione
    return HttpResponse("Register View Placeholder")


# --- CLASSI CUSTOM PER IL FLUSSO DI RESET PASSWORD (SOLUZIONE EMAILJS) ---

class CustomPasswordResetView(DjangoPasswordResetView):
    """Override per usare il form custom e il template corretto."""
    form_class = CustomPasswordResetForm
    template_name = 'registration/password_reset_form.html'
    
    # Non usiamo email_template_name perché l'invio è esterno (API)
    subject_template_name = 'registration/password_reset_subject.txt' 
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        
        # Chiama la funzione originale di Django che gestisce il reindirizzamento
        response = super().form_valid(form)
        
        # === INIZIO LOGICA PER EMAILJS (Integrazione API) ===
        try:
            user_email = form.cleaned_data['email']
            
            # Replicare la ricerca che Django ha fatto per trovare l'utente corretto
            users = User.objects.filter(email=user_email)
            
            if users.exists():
                user = users[0] 
                current_site = get_current_site(self.request)
                
                # 1. Genera UID e Token (usando il generatore standard di Django)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = self.token_generator.make_token(user) 
                protocol = 'https' if self.request.is_secure() else 'http'
                
                # 2. COSTRUZIONE DEL LINK COMPLETO
                reset_link_url = f"{protocol}://{current_site.domain}{reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"
                
                # 3. PREPARAZIONE DEL PAYLOAD JSON PER L'INVIO API
                emailjs_payload = {
                    'username': user.username,
                    'user_name': user.get_full_name() or user.username,
                    'recipient_email': user.email,
                    'reset_link': reset_link_url, # <--- La variabile da usare in EmailJS
                    'platform_name': current_site.name
                }
                
                # 4. CHIAMATA ALLA FUNZIONE DI INVIO EMAILJS
                # Questa funzione recupera le credenziali dal DB
                send_email_via_emailjs(emailjs_payload)
            
        except Exception as e:
            # Cattura qualsiasi errore nella logica di invio API
            print(f"ERRORE SISTEMA EMAILJS (Debug): {e}")
            messages.error(self.request, f"Errore critico nell'invio dell'email di reset.")
        # === FINE LOGICA EMAILJS ===
        
        # Ritorna la risposta standard che reindirizza a password_reset_done
        return response


class CustomPasswordResetDoneView(DjangoPasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

class CustomPasswordResetConfirmView(DjangoPasswordResetConfirmView):
    form_class = CustomSetPasswordForm
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(DjangoPasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'
    
    
# ==============================================================================
# 2. VISTE STUDENTE E PROFILO
# ==============================================================================

@login_required
def dashboard_studente(request):
    """
    Gestisce il reindirizzamento degli utenti loggati (URL '/').
    """
    user = request.user
    
    # Smistamento ruoli
    if user.is_superuser or user.ruolo == 'ADMIN':
        return redirect('admin:index')
    
    if user.ruolo == 'CONSULENTE':
        return redirect('dashboard_consulente') 
    
    if user.ruolo == 'REFERENTE':
        return redirect('dashboard_compliance') 
    
    # Logica STUDENTE
    try:
        # PLACEHOLDER: Recupera i dati del corso dello studente
        iscrizioni = []
    except Exception:
        iscrizioni = []
        
    context = {
        'iscrizioni_list': iscrizioni,
        'studente_name': user.get_full_name() or user.username
    }
    
    return render(request, 'dashboard_studente.html', context)


@login_required
@user_passes_test(is_profilo_user)
def profilo_utente(request): 
    """
    Vista unificata per la gestione e l'aggiornamento dei dati personali 
    di tutti i ruoli non-staff.
    """
    user = request.user
    
    # 1. Seleziona il Form e il Template in base al Ruolo
    if user.ruolo == 'CONSULENTE':
        ProfiloFormClass = ConsulenteUpdateForm
        template_name = 'user_auth/profilo_consulente.html' 
    elif user.ruolo == 'REFERENTE':
        ProfiloFormClass = ReferenteUpdateForm
        template_name = 'user_auth/profilo_referente.html' 
    elif user.ruolo == 'STUDENTE':
        ProfiloFormClass = ProfiloStudenteForm 
        template_name = 'profilo_studente_placeholder.html'
    else:
        return redirect('dashboard_compliance') 

    # 2. Gestione dei Forms
    
    if request.method == 'POST' and 'submit_profilo' in request.POST:
        profilo_form = ProfiloFormClass(request.POST, instance=user)
        if profilo_form.is_valid():
            profilo_form.save()
            messages.success(request, "Dati profilo aggiornati con successo.")
            return redirect('profilo_utente')
    else:
        profilo_form = ProfiloFormClass(instance=user)

    if request.method == 'POST' and 'submit_password' in request.POST:
        password_form = PasswordChangeForm(user=user, data=request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user) 
            messages.success(request, "Password aggiornata con successo!")
            return redirect('profilo_utente')
    else:
        password_form = PasswordChangeForm(user=user)

    # 3. Renderizza il template specifico
    return render(request, template_name, {
        'profilo_form': profilo_form,
        'password_form': password_form,
        'user': user,
        'titolo_pagina': _("Gestione Profilo")
    })


@login_required
def profilo_update(request):
    # PLACEHOLDER: Logica di update
    return HttpResponse("Profilo Update Placeholder")


# ==============================================================================
# 3. VISTE ADMIN/REPORTING (EXPORT EXCEL)
# ==============================================================================

@user_passes_test(is_admin)
def export_aziende_excel(request):
    """Estrae i dati di tutte le aziende e li esporta in un file Excel."""
    # PLACEHOLDER: Logica di export
    return HttpResponse("Export Aziende Excel Placeholder")


# ==============================================================================
# 4. VISTE ADMIN (Importazione Excel - PLACEHOLDER)
# ==============================================================================

def import_student_excel(request):
    """Placeholder per l'importazione Excel (logica spostata in compliance)."""
    return HttpResponse("Import Student Excel View Placeholder")