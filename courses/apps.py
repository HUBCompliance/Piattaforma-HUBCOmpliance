from django.apps import AppConfig
# --- AGGIUNTA CHIAVE: Import per la traduzione ---
from django.utils.translation import gettext_lazy as _

class CoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courses'
    # --- AGGIUNTA CHIAVE: Nome visualizzato nell'Admin ---
    verbose_name = _("Gestione E-Learning")