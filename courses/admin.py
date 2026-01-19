from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Corso, Modulo, Media,
    Quiz, Domanda, Risposta,
    IscrizioneCorso, ProgressoModulo, Attestato,
    ImpostazioniSito, CategoriaCorso
)

# ==============================================================================
# 0. INLINES (Per gestire tutto insieme)
# ==============================================================================

class MediaInline(admin.TabularInline):
    model = Media
    extra = 1
    # CORREZIONE: Uso 'nome' e 'file' come definito nel tuo models.py
    fields = ('nome', 'file') 

class RispostaInline(admin.TabularInline):
    model = Risposta
    extra = 3  
    fields = ('testo', 'is_corretta')

class DomandaInline(admin.StackedInline):
    model = Domanda
    extra = 1
    fields = ('testo', 'ordine')

class ModuloInline(admin.StackedInline):
    model = Modulo
    extra = 1
    fields = ('titolo', 'ordine', 'durata_minuti')

# ==============================================================================
# 1. CONFIGURAZIONE IMPOSTAZIONI SITO
# ==============================================================================

@admin.register(ImpostazioniSito)
class ImpostazioniSitoAdmin(admin.ModelAdmin):
    readonly_fields = ('pk',)
    list_display = ['nome_piattaforma', 'dehashed_email']
    
    fieldsets = (
        (_('Branding & UI'), {
            'fields': ('pk', 'nome_piattaforma', 'logo_principale', ('colore_primario', 'colore_secondario'))
        }),
        (_('Cybersecurity & NIS2 (DeHashed)'), {
            'fields': (('dehashed_email', 'dehashed_api_key'),)
        }),
        (_('AI & Compliance'), {
            'fields': ('gemini_api_key', 'template_nomina_csirt')
        }),
        (_('Email Service (EmailJS)'), {
            'fields': ('email_service_id', 'emailjs_template_id_allerta', ('email_public_key', 'email_private_key'), ('email_template_id', 'email_reset_template_id'), ('email_fornitori_template_id', 'email_scadenza_template_id', 'email_scadenza_compito_id'))
        }),
        (_('Strumenti Analisi Esterni'), {
            'fields': (('pentest_tools_api_key', 'pentest_tools_api_url'), 'viewdns_api_key')
        }),
    )

    def has_add_permission(self, request):
        return not ImpostazioniSito.objects.exists()

# ==============================================================================
# 2. GESTIONE CORSI, MODULI E QUIZ
# ==============================================================================

@admin.register(Corso)
class CorsoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'stato', 'is_obbligatorio')
    list_filter = ('stato', 'categoria', 'is_obbligatorio')
    search_fields = ('nome', 'descrizione')
    inlines = [ModuloInline]

@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ('titolo', 'corso', 'ordine')
    list_filter = ('corso',)
    inlines = [MediaInline]

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('modulo', 'titolo', 'punteggio_minimo')
    inlines = [DomandaInline]

@admin.register(Domanda)
class DomandaAdmin(admin.ModelAdmin):
    list_display = ('testo', 'quiz', 'ordine')
    list_filter = ('quiz',)
    inlines = [RispostaInline]

# ==============================================================================
# 3. REGISTRAZIONE MODELLI DI SERVIZIO
# ==============================================================================

@admin.register(CategoriaCorso)
class CategoriaCorsoAdmin(admin.ModelAdmin):
    list_display = ('nome',)

@admin.register(IscrizioneCorso)
class IscrizioneCorsoAdmin(admin.ModelAdmin):
    list_display = ('studente', 'corso', 'data_iscrizione', 'completato')
    list_filter = ('completato', 'corso')

@admin.register(Attestato)
class AttestatoAdmin(admin.ModelAdmin):
    # CORREZIONE: Uso 'data_rilascio' perché 'data_emissione' NON ESISTE nel tuo modello
    list_display = ('iscrizione', 'codice_univoco', 'data_rilascio')
    readonly_fields = ('data_rilascio',)

@admin.register(ProgressoModulo)
class ProgressoModuloAdmin(admin.ModelAdmin):
    list_display = ('iscrizione', 'modulo', 'completato', 'data_completamento')
