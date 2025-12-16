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


    def send_messages(self, email_messages):
        """Invia un elenco di messaggi email tramite l'API EmailJS."""
        
        if not self.config:
            if not self.fail_silently:
                 raise Exception("Impossibile caricare la configurazione EmailJS dal database.")
            return 0
        
        service_id = self.config.email_service_id
        public_key = self.config.email_public_key
        private_key = self.config.email_private_key # Access Token
        
        if not service_id or not private_key or not public_key:
            print("[EmailBackend] ERRORE: Service ID, Public Key, o Private Key EmailJS mancano.")
            if not self.fail_silently:
                raise Exception("EmailJS Service ID, Public Key o Private Key non sono impostati.") 
            return 0

        num_sent = 0
        
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