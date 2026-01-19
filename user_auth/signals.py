import requests
import json
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import AuditLog
from courses.models import ImpostazioniSito

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    AuditLog.objects.create(
        utente=user,
        azione='LOGIN',
        modello='Autenticazione',
        descrizione="Accesso effettuato con successo.",
        indirizzo_ip=request.META.get('REMOTE_ADDR')
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        AuditLog.objects.create(
            utente=user,
            azione='LOGOUT',
            modello='Autenticazione',
            descrizione="Uscita effettuata correttamente.",
            indirizzo_ip=request.META.get('REMOTE_ADDR')
        )

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    ip_attuale = request.META.get('REMOTE_ADDR') if request else '0.0.0.0'
    username_tentato = credentials.get('username', 'Sconosciuto')
    
    # 1. Registriamo il fallimento attuale
    AuditLog.objects.create(
        utente=None,
        azione='LOGIN_FAILED',
        modello='Sicurezza',
        descrizione=f"TENTATIVO DI ACCESSO FALLITO per username: {username_tentato}",
        indirizzo_ip=ip_attuale
    )

    # 2. Definiamo una finestra temporale stretta (es. 5 minuti invece di 10)
    # per evitare che errori vecchi accumulati facciano scattare la mail
    finestra_temporale = timezone.now() - timedelta(minutes=5)
    
    # 3. Contiamo i fallimenti SOLO di questo IP e SOLO in questa finestra
    tentativi_recenti = AuditLog.objects.filter(
        azione='LOGIN_FAILED',
        indirizzo_ip=ip_attuale,
        data_ora__gte=finestra_temporale
    ).count()

    print(f"DEBUG: Tentativi recenti rilevati per {ip_attuale}: {tentativi_recenti}")

    # 4. Facciamo scattare la mail SOLO al raggiungimento esatto della soglia (es. ogni 5)
    # Usando l'operatore modulo (%) evitiamo che mandi una mail a ogni tentativo (6, 7, 8...)
    if tentativi_recenti > 0 and tentativi_recenti % 5 == 0:
        print(f"DEBUG: Soglia raggiunta ({tentativi_recenti}). Invio allerta...")
        invia_allerta_bruteforce_emailjs(ip_attuale, username_tentato, tentativi_recenti)

def invia_allerta_bruteforce_emailjs(ip, username, conteggio):
    config = ImpostazioniSito.objects.first()
    
    if not config or not config.emailjs_template_id_allerta:
        print("DEBUG: Configurazione Allerta mancante in ImpostazioniSito.")
        return

    url = "https://api.emailjs.com/api/v1.0/email/send"
    
    # PAYLOAD AGGIORNATO CON I NOMI CAMPI REALI DEL TUO MODELLO
    payload = {
        'service_id': config.email_service_id, 
        'template_id': config.emailjs_template_id_allerta, 
        'user_id': config.email_public_key,
        'accessToken': config.email_private_key, 
        'template_params': {
            'subject': '⚠️ ALLERTA SICUREZZA: Brute Force Rilevato',
            'ip_address': ip,
            'attempts': conteggio,
            'target_username': username,
            'timestamp': timezone.now().strftime('%d/%m/%Y %H:%M:%S'),
            'admin_email': 'tua_email@esempio.it' # Inserisci qui l'email del destinatario
        }
    }

    try:
        response = requests.post(
            url, 
            data=json.dumps(payload), 
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 200:
            print("DEBUG: Email di allerta inviata con successo via EmailJS!")
        else:
            print(f"DEBUG: Errore EmailJS ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"DEBUG: Errore connessione EmailJS: {e}")