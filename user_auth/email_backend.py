import requests
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
from django.utils.translation import gettext_lazy as _

# Importiamo il modello ImpostazioniSito
try:
    from courses.models import ImpostazioniSito
except ImportError:
    ImpostazioniSito = None
except Exception as e:
    print(f"[EmailBackend] ERRORE CRITICO: Impossibile importare ImpostazioniSito: {e}")
    ImpostazioniSito = None


class EmailJSBackend(BaseEmailBackend):
    """Backend di posta elettronica personalizzato che utilizza l'API EmailJS per inviare email."""

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)

        self.config = None

        # 1. Tenta di caricare le impostazioni singleton
        if ImpostazioniSito is not None:
            try:
                # Usa .objects.get()
                self.config = ImpostazioniSito.objects.get(pk=1)
            except ImpostazioniSito.DoesNotExist:
                print("[EmailBackend] ERRORE: L'istanza ImpostazioniSito non è stata trovata (pk=1).")
            except Exception as e:
                print(f"[EmailBackend] ERRORE: Impossibile caricare ImpostazioniSito: {e}")

        # 2. Inizializzazione API Base
        self.base_url = "https://api.emailjs.com/api/v1.0/email/send"


    # Nel tuo file del backend email
def send_messages(self, email_messages):
        if not self.config:
            return 0

        num_sent = 0
        for email_message in email_messages:
            try:
                # 1. Prendiamo il corpo originale
                original_body = email_message.body

                # 2. SOSTITUZIONE MANUALE TOTALE
                # Non chiediamo a Django, scriviamo noi l'URL sopra quello sbagliato
                clean_body = original_body.replace("http://127.0.0.1:8000", "https://gmuggit.pythonanywhere.com")
                clean_body = clean_body.replace("http://localhost:8000", "https://gmuggit.pythonanywhere.com")

                # 3. LOG DI SICUREZZA (Questo DEVI vederlo nel log se funziona)
                print(f">>> [FILTRO BACKEND] Controllo email per: {email_message.recipients()}")
                if "127.0.0.1" in original_body:
                    print(">>> [ATTENZIONE] Link 127.0.0.1 rilevato e rimpiazzato con https://gmuggit.pythonanywhere.com")

                payload = {
                    "service_id": self.config.email_service_id,
                    "template_id": self.config.email_reset_template_id,
                    "user_id": self.config.email_public_key,
                    "accessToken": self.config.email_private_key,
                    "template_params": {
                        "to_email": email_message.recipients()[0],
                        "subject": email_message.subject,
                        "message_html": clean_body, # MANDIAMO IL TESTO PULITO
                        "reset_link_placeholder": clean_body,
                        "action_url": "https://gmuggit.pythonanywhere.com"
                    }
                }

                response = requests.post(self.base_url, json=payload, timeout=10)
                response.raise_for_status()
                num_sent += 1
            except Exception as e:
                print(f">>> [ERRORE BACKEND] Fallimento: {e}")
        return num_sent
        for email_message in email_messages:
            try:
                email_subject = email_message.subject
                recipient_list = email_message.recipients()

                template_to_use = self.config.email_template_id # Default
                subject_lower = email_subject.lower()

                # Variabile per il link di reset/dettagli (estraiamo tutto il corpo)
                reset_link_content = email_message.body

                # =========================================================
                # 🛠️ LOGICA DI SELEZIONE DEL TEMPLATE
                # =========================================================
                is_reset_email = False
                if "password reset" in subject_lower or "reimposta password" in subject_lower or "imposta password" in subject_lower or "set password" in subject_lower:
                    template_to_use = self.config.email_reset_template_id
                    is_reset_email = True # Flag se è un reset

                elif "compito" in subject_lower or "task" in subject_lower or "scadenza compito" in subject_lower:
                    template_to_use = self.config.email_scadenza_compito_id

                elif "scadenza corso" in subject_lower or "contratto in scadenza" in subject_lower:
                    template_to_use = self.config.email_scadenza_template_id


                if not template_to_use:
                    print(f"[EmailJS Error] Template ID mancante per l'oggetto: {email_subject}")
                    continue
                # =========================================================

                # Payload (Assicurati che il tuo template EmailJS lato API usi i campi sottostanti)
                payload = {
                    "service_id": service_id,
                    "template_id": template_to_use,
                    "user_id": public_key,
                    "accessToken": private_key,
                    "template_params": {
                        "to_email": recipient_list[0] if recipient_list else "no-recipient@example.com",
                        "subject": email_subject,

                        # PASSO IL CORPO COMPLETO IN UNA VARIABILE SPECIFICA PER IL RESET
                        "reset_link_placeholder": reset_link_content if is_reset_email else None,

                        # Uso message_html per gli altri messaggi (o per visualizzare il corpo generico)
                        "message_html": email_message.body,

                        # Il template EmailJS deve usare {{ reset_link_placeholder }} o {{ message_html }}
                    }
                }

                # 5. Invio della Richiesta
                response = requests.post(self.base_url, json=payload)
                response.raise_for_status()

                num_sent += 1

            except requests.exceptions.RequestException as e:
                print(f"[EmailJS Error] Richiesta fallita: {e}")
                if not self.fail_silently:
                    raise
            except Exception as e:
                print(f"[EmailJS Error] Errore imprevisto durante l'invio: {e}")
                if not self.fail_silently:
                    raise

        return num_sent