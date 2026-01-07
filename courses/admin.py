from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Corso, Modulo, Media,
    Quiz, Domanda, Risposta,
    IscrizioneCorso, ProgressoModulo, Attestato,
    ImpostazioniSito, CategoriaCorso
)

# ==============================================================================
# CONFIGURAZIONE IMPOSTAZIONI SITO (OTTIMIZZATA PER DEHASHED)
# ==============================================================================

@admin.register(ImpostazioniSito)
class ImpostazioniSitoAdmin(admin.ModelAdmin):
    readonly_fields = ('pk',)
    list_display = ['nome_piattaforma', 'dehashed_email']
    
    # Organizzazione dei campi per la Governance di Ferrari Spa
    fields = (
        'pk',
        # --- BRANDING ---
        'nome_piattaforma',
        'logo_principale',
        ('colore_primario', 'colore_secondario'),
        
        # --- MONITORAGGIO DATA BREACH (DEHASHED - NIS2) ---
        ('dehashed_email', 'dehashed_api_key'), # Campi per l'integrazione DeHashed
        
        # --- AI & COMPLIANCE ---
        'gemini_api_key',
        'template_nomina_csirt',

        
        # --- NOTIFICHE EMAIL ---
        'email_service_id',
        ('email_public_key', 'email_private_key'),
        ('email_template_id', 'email_reset_template_id'),
    
        # --- ANALISI VULNERABILITÀ (STRUMENTI ESTERNI) ---
        ('pentest_tools_api_key', 'pentest_tools_api_url'),
        'viewdns_api_key',  # <--- Aggiungiamo questa riga
    )
    def has_add_permission(self, request):
        return not ImpostazioniSito.objects.exists()

# ==============================================================================
# REGISTRAZIONE ALTRI MODELLI (INVARIATA)
# ==============================================================================

@admin.register(CategoriaCorso)
class CategoriaCorsoAdmin(admin.ModelAdmin):
    list_display = ('nome',)

@admin.register(Corso)
class CorsoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'categoria', 'stato', 'is_obbligatorio']
    list_filter = ['stato', 'categoria']

admin.site.register(Modulo)
admin.site.register(Media)
admin.site.register(Quiz)
admin.site.register(Domanda)
admin.site.register(Risposta)
admin.site.register(IscrizioneCorso)
admin.site.register(ProgressoModulo)
admin.site.register(Attestato)