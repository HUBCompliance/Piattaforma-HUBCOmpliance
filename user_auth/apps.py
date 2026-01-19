from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.apps import AppConfig

class UserAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_auth'
    # --- MODIFICA CHIAVE ---
    # Questo è il nome che apparirà nell'admin
    verbose_name = _('Gestione Utenti e Aziende')
    # -----------------------

    def ready(self):
        # Questo comando dice a Django di andare a leggere il file signals.py
        import user_auth.signals
class UserAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_auth'

    def ready(self):
        import user_auth.signals  # <--- Fondamentale: carica il file creato sopra        