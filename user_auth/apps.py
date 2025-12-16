from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class UserAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_auth'
    # --- MODIFICA CHIAVE ---
    # Questo è il nome che apparirà nell'admin
    verbose_name = _('Gestione Utenti e Aziende')
    # -----------------------

    def ready(self):
        try:
            import user_auth.models  
        except ImportError:
            pass