from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import (
    PasswordResetView as DjangoPasswordResetView,
    PasswordResetDoneView as DjangoPasswordResetDoneView,
    PasswordResetConfirmView as DjangoPasswordResetConfirmView,
    PasswordResetCompleteView as DjangoPasswordResetCompleteView,
)
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.signals import user_login_failed  # <--- Importa il segnale

import requests
import logging

# Importazioni locali (Modelli e Form)
from .models import CustomUser as User, Azienda, Consulente
from .forms import (
    LoginForm, RegisterForm, CustomPasswordResetForm,
    ReferenteUpdateForm, ConsulenteUpdateForm, ProfiloStudenteForm
)

logger = logging.getLogger(__name__)

# --- HELPER FUNCTIONS ---

def trigger_set_password_email(request, user):
    """
    Invia l'email tramite EmailJS forzando l'URL di produzione.
    L'importazione di ImpostazioniSito è interna per evitare circular imports.
    """
    from courses.models import ImpostazioniSito

    try:
        # Generazione UID e Token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # URL FORZATO DI PRODUZIONE - Nessun calcolo automatico per evitare 127.0.0.1
        action_url = f"https://gmuggit.pythonanywhere.com/reset/{uid}/{token}/"

        # Recupero configurazione EmailJS
        config = ImpostazioniSito.objects.first()
        if not config:
            print(">>> [ERRORE CRITICO] Tabella ImpostazioniSito vuota nel database!")
            return False

        payload = {
            'service_id': config.email_service_id,
            'template_id': config.email_template_id,
            'user_id': config.email_public_key,
            'accessToken': config.email_private_key,
            'template_params': {
                'user_name': user.username,
                'to_email': user.email,
                'action_url': action_url
            }
        }

        # LOG DI CONTROLLO IN TEMPO REALE (Visibili nel server.log di PythonAnywhere)
        print(f"\n>>> [TEST-FINALE-PRODUZIONE] Destinatario: {user.email}")
        print(f">>> [INVIO EMAILJS] URL Produzione: {action_url}")

        response = requests.post(
            "https://api.emailjs.com/api/v1.0/email/send",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            print(f">>> [SUCCESS] EmailJS ha accettato la richiesta per {user.email}\n")
            return True
        else:
            print(f">>> [ERROR] EmailJS errore {response.status_code}: {response.text}\n")
            return False

    except Exception as e:
        print(f">>> [EXCEPTION] Errore in trigger_set_password_email: {str(e)}\n")
        return False

def is_profilo_user(user):
    return user.is_authenticated and user.ruolo in ['STUDENTE', 'REFERENTE', 'CONSULENTE']

# --- VISTE DI AUTENTICAZIONE ---

def login_view(request):
    if request.user.is_authenticated:
        # Usa redirect_after_login per coerenza
        return redirect_after_login(request.user)

    if request.method == 'POST':
        from django.contrib.auth import authenticate # Assicurati che sia importato
        email = request.POST.get('username') # Il LoginForm di solito usa 'username' o 'email'
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect_after_login(user)
        else:
            messages.error(request, "Credenziali non valide.")
    
    return render(request, 'registration/login.html', {'form': LoginForm()})
def redirect_after_login(user):
    if user.ruolo == 'CONSULENTE':
        return redirect('compliance:dashboard_consulente')
    elif user.ruolo == 'REFERENTE':
        return redirect('compliance:dashboard_compliance')
    elif user.ruolo == 'STUDENTE':
        # Qui usa il nome corretto definito nel tuo urls.py
        return redirect('compliance:dashboard_studente') 
    else:
        return redirect('/')

def logout_view(request):
    logout(request)
    return redirect('/login/')

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registrazione effettuata con successo. Ora puoi accedere.")
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})

# --- DASHBOARD E PROFILO ---

@login_required
def dashboard_studente(request):
    user = request.user
    from courses.models import IscrizioneCorso # Import locale

    if user.ruolo == 'REFERENTE':
        return redirect('compliance:dashboard_compliance')

    iscrizioni = IscrizioneCorso.objects.filter(studente=user).select_related('corso')
    return render(request, 'dashboard_studente.html', {
        'iscrizioni': iscrizioni,
        'studente_name': user.username
    })

@login_required
@user_passes_test(is_profilo_user)
def profilo_utente(request):
    user = request.user
    if user.ruolo == 'CONSULENTE':
        form_class, template = ConsulenteUpdateForm, 'user_auth/profilo_consulente.html'
    elif user.ruolo == 'REFERENTE':
        form_class, template = ReferenteUpdateForm, 'user_auth/profilo_referente.html'
    else:
        form_class, template = ProfiloStudenteForm, 'profilo_studente_placeholder.html'

    p_form = form_class(instance=user)
    pw_form = PasswordChangeForm(user=user)

    if request.method == 'POST':
        if 'submit_profilo' in request.POST:
            p_form = form_class(request.POST, instance=user)
            if p_form.is_valid():
                p_form.save()
                messages.success(request, "Profilo aggiornato.")
        elif 'submit_password' in request.POST:
            pw_form = PasswordChangeForm(user=user, data=request.POST)
            if pw_form.is_valid():
                user = pw_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password aggiornata.")

    return render(request, template, {
        'profilo_form': p_form,
        'password_form': pw_form,
        'titolo_pagina': "Gestione Profilo"
    })

# --- VISTE PERSONALIZZATE RESET PASSWORD ---

class CustomPasswordResetView(DjangoPasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'registration/password_reset_form.html'
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        # Sovrascriviamo per evitare l'invio SMTP standard di Django
        email = form.cleaned_data.get('email')
        user = User.objects.filter(email=email).first()

        if user:
            trigger_set_password_email(self.request, user)

        return redirect(self.success_url)

class CustomPasswordResetDoneView(DjangoPasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

class CustomPasswordResetConfirmView(DjangoPasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'

class CustomPasswordResetCompleteView(DjangoPasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'

# --- EXPORT ---

def export_aziende_excel(request):
    return HttpResponse("Logica di esportazione aziende non ancora implementata.")