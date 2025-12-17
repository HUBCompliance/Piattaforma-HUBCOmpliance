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
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse, JsonResponse 
import requests

# Importazioni locali
from .models import CustomUser as User, Azienda, Consulente
from .forms import (
    LoginForm, RegisterForm, CustomPasswordResetForm, 
    ReferenteUpdateForm, ConsulenteUpdateForm, ProfiloStudenteForm
)

# Importazioni da app esterne
from courses.models import ImpostazioniSito, IscrizioneCorso

# --- HELPER FUNCTIONS ---

def trigger_set_password_email(request, user):
    """Invia l'email per impostare la password iniziale (richiesta da compliance)."""
    try:
        current_site = get_current_site(request)
        from django.contrib.auth.tokens import default_token_generator
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        protocol = 'https' if request.is_secure() else 'http'
        action_url = f"{protocol}://{current_site.domain}{reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"
        
        config = ImpostazioniSito.objects.first()
        payload = {
            'service_id': config.email_service_id,
            'template_id': config.email_template_id,
            'user_id': config.email_public_key,
            'accessToken': config.email_private_key,
            'template_params': {'user_name': user.username, 'to_email': user.email, 'action_url': action_url}
        }
        requests.post("https://api.emailjs.com/api/v1.0/email/send", json=payload, timeout=10)
        return True
    except:
        return False

def is_profilo_user(user):
    return user.is_authenticated and user.ruolo in ['STUDENTE', 'REFERENTE', 'CONSULENTE']


def is_consulente_user(user):
    """Ritorna True solo se l'utente è marcato come consulente *e* ha un profilo Consulente valido."""
    if user.ruolo != 'CONSULENTE':
        return False
    try:
        # Evita redirect errati di studenti che hanno il ruolo impostato in modo non coerente
        return bool(user.consulente)
    except Consulente.DoesNotExist:
        return False


def get_dashboard_redirect(user):
    """Restituisce il nome della dashboard in base al ruolo dell'utente."""
    if is_consulente_user(user):
        return 'dashboard_consulente'
    if user.ruolo == 'REFERENTE':
        return 'dashboard_compliance'
    if user.is_staff:
        return 'admin:index'
    # Tutti gli altri ruoli (o valori inattesi) vengono trattati come Studenti
    return 'dashboard_studente'

# --- VISTE PRINCIPALI ---

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Smista l'utente alla dashboard corretta in base al ruolo
            return redirect(get_dashboard_redirect(user))
    return render(request, 'registration/login.html', {'form': LoginForm()})

def logout_view(request):
    logout(request)
    return redirect('/login/') 

def register_view(request):
    return render(request, 'registration/register.html', {'form': RegisterForm()})

@login_required
def dashboard_studente(request):
    user = request.user

    # Smistamento robusto per evitare redirect errati
    dashboard_target = get_dashboard_redirect(user)
    if dashboard_target != 'dashboard_studente':
        return redirect(dashboard_target)

    # Se è uno STUDENTE, deve caricare questo:
    iscrizioni = IscrizioneCorso.objects.filter(studente=user).select_related('corso')
    return render(request, 'dashboard_studente.html', {
        'iscrizioni_list': iscrizioni,
        'studente_name': user.username
    })

@login_required
@user_passes_test(is_profilo_user)
def profilo_utente(request): 
    """Vista del profilo (Risolve l'AttributeError)."""
    user = request.user
    if user.ruolo == 'CONSULENTE':
        form_class, template = ConsulenteUpdateForm, 'user_auth/profilo_consulente.html'
    elif user.ruolo == 'REFERENTE':
        form_class, template = ReferenteUpdateForm, 'user_auth/profilo_referente.html'
    else:
        form_class, template = ProfiloStudenteForm, 'profilo_studente.html'

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

# --- RESET PASSWORD ---
class CustomPasswordResetView(DjangoPasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'registration/password_reset_form.html'
    def form_valid(self, form):
        response = super().form_valid(form)
        user = User.objects.filter(email=form.cleaned_data['email']).first()
        if user: trigger_set_password_email(self.request, user)
        return response

class CustomPasswordResetDoneView(DjangoPasswordResetDoneView): template_name = 'registration/password_reset_done.html'
class CustomPasswordResetConfirmView(DjangoPasswordResetConfirmView): template_name = 'registration/password_reset_confirm.html'
class CustomPasswordResetCompleteView(DjangoPasswordResetCompleteView): template_name = 'registration/password_reset_complete.html'

def export_aziende_excel(request):
    return HttpResponse("Export logic...")