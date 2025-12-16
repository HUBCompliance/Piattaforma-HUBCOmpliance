# setup_admin.py

from django.contrib import admin
from django.contrib.auth.models import Group # <--- CRUCIALE: Aggiungi Group qui
    
# Importa tutti i tuoi modelli (usando il nome d'app 'user_auth' e 'courses')
from user_auth.models import CustomUser 
from courses.models import Azienda, Corso, Modulo, Media, IscrizioneCorso, ProgressoModulo


def register_all():
    """Esegue una registrazione manuale e forzata dei modelli."""
    
    # Registrazione semplice dei modelli Custom
    admin.site.register(CustomUser)
    admin.site.register(Azienda)
    admin.site.register(Corso)
    admin.site.register(Modulo)
    admin.site.register(Media)
    admin.site.register(IscrizioneCorso)
    admin.site.register(ProgressoModulo)

    # Registra i modelli standard di Django (Gruppi)
    admin.site.register(Group) 
    
register_all()