from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Corso, Modulo, Media,
    Quiz, Domanda, Risposta,
    IscrizioneCorso, ProgressoModulo, Attestato,
    ImpostazioniSito, CategoriaCorso
)

# ==============================================================================
# INLINES
# ==============================================================================

class ModuloInline(admin.TabularInline):
    model = Modulo
    extra = 1
    fields = ('titolo', 'ordine', 'durata_minuti')
    ordering = ('ordine',)

class DomandaInline(admin.TabularInline):
    model = Domanda
    extra = 1
    fields = ('testo', 'ordine')
    ordering = ('ordine',)

class RispostaInline(admin.TabularInline):
    model = Risposta
    extra = 2
    fields = ('testo', 'is_corretta')

class ProgressoModuloInline(admin.TabularInline):
    model = ProgressoModulo
    extra = 0
    readonly_fields = ('data_completamento',)
    can_delete = False


# ==============================================================================
# ADMIN MODELS
# ==============================================================================

@admin.register(CategoriaCorso)
class CategoriaCorsoAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(Corso)
class CorsoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'categoria', 'stato', 'durata_ore', 'is_obbligatorio']
    list_filter = ['stato', 'categoria', 'is_obbligatorio']
    inlines = [ModuloInline]
    search_fields = ['nome', 'descrizione']

@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ['corso', 'titolo', 'ordine', 'durata_minuti']
    list_filter = ['corso']
    search_fields = ['titolo', 'contenuto_html']

@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'modulo', 'file']
    list_filter = ['modulo__corso']
    search_fields = ['nome']
    
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['modulo', 'titolo', 'punteggio_minimo']
    list_filter = ['modulo__corso']
    inlines = [DomandaInline]
    search_fields = ['titolo']

@admin.register(Domanda)
class DomandaAdmin(admin.ModelAdmin):
    list_display = ['testo', 'quiz']
    list_filter = ['quiz'] 
    search_fields = ['testo']
    inlines = [RispostaInline]

@admin.register(IscrizioneCorso)
class IscrizioneCorsoAdmin(admin.ModelAdmin):
    list_display = ['studente', 'corso', 'data_iscrizione', 'completato', 'data_completamento']
    list_filter = ['corso', 'completato']
    search_fields = ['studente__username', 'corso__nome']
    inlines = [ProgressoModuloInline]

@admin.register(Attestato)
class AttestatoAdmin(admin.ModelAdmin):
    list_display = ['codice_univoco', 'iscrizione', 'data_rilascio']
    search_fields = ['codice_univoco', 'iscrizione__studente__username']
    readonly_fields = ['codice_univoco', 'data_rilascio', 'iscrizione']

@admin.register(ImpostazioniSito)
class ImpostazioniSitoAdmin(admin.ModelAdmin):
    # Campo pk per visualizzazione, non per modifica
    readonly_fields = ('pk',) 
    
    # Rimuoviamo la proprietà list_display per il rendering del form singolo
    list_display = ['nome_piattaforma', 'colore_primario']
    
    # === LISTA COMPLETA DEI CAMPI (Inclusi quelli nuovi) ===
    fields = (
        'pk', 
        'nome_piattaforma', 
        'colore_primario', 
        'colore_secondario', 
        'logo_principale', 
        'template_nomina_csirt', # <--- AGGIUNTO: Ora sarà visibile!
        'gemini_api_key', 
        'dehashed_username',
        'dehashed_api_key',
        'pentest_tools_api_key',
        'pentest_tools_base_url',
        'pentest_tools_scan_path',
        'email_service_id', 
        'email_public_key', 
        'email_private_key', 
        'email_template_id', 
        'email_reset_template_id', 
        'email_scadenza_template_id', 
        'email_scadenza_compito_id', 
    )
    
    # Questo override garantisce che ci sia solo un'istanza (pk=1)
    def has_delete_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request):
        return not ImpostazioniSito.objects.exists() or ImpostazioniSito.objects.count() == 0
