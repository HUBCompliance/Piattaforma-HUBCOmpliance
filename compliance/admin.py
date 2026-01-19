from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

# Import per Export Excel
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportActionModelAdmin
from import_export.admin import ExportActionModelAdmin

# Import Modelli
from user_auth.models import AuditLog, CustomUser
from .models import (
    Trattamento, DocumentoAziendale, VersioneDocumento,
    Incidente, RichiestaInteressato, AuditSession, AuditDomanda, 
    AuditCategoria, AuditRisposta, Compito, Asset, Software, 
    RuoloPrivacy, Paese, ValutazioneTIA, Videosorveglianza,
    ReferenteCSIRT, NotificaIncidente,
    CategoriaDati, SoggettoInteressato, ConfigurazioneRete, ComponenteRete,
    SecurityControl, SecurityAudit, SecurityResponse, Fornitore
)

# ==============================================================================
# 0. RISORSA PER EXPORT AUDIT LOG (Necessaria per AuditLogAdmin)
# ==============================================================================
class AuditLogResource(resources.ModelResource):
    utente = fields.Field(
        column_name='Utente',
        attribute='utente',
        widget=ForeignKeyWidget(CustomUser, 'username')
    )
    class Meta:
        model = AuditLog
        fields = ('data_ora', 'utente', 'azione', 'modello', 'descrizione', 'indirizzo_ip')
        export_order = ('data_ora', 'utente', 'azione', 'modello', 'descrizione', 'indirizzo_ip')

# ==============================================================================
# 1. ADMIN PER MODELLI BASE e TRATTAMENTI
# ==============================================================================

@admin.register(CategoriaDati)
class CategoriaDatiAdmin(admin.ModelAdmin):
    search_fields = ('nome',)

@admin.register(SoggettoInteressato)
class SoggettoInteressatoAdmin(admin.ModelAdmin):
    search_fields = ('nome',)

@admin.register(Trattamento)
class TrattamentoAdmin(admin.ModelAdmin):
    list_display = ('nome_trattamento', 'azienda', 'tipo_ruolo', 'livello_rischio', 'dpia_necessaria')
    list_filter = ('tipo_ruolo', 'livello_rischio', 'dpia_necessaria', 'azienda')
    search_fields = ('nome_trattamento', 'finalita')
    filter_horizontal = ('categorie_dati', 'soggetti_interessati',)
    
    fieldsets = (
        (_('Informazioni di Base'), {
            'fields': ('azienda', 'nome_trattamento', 'tipo_ruolo', 'per_conto_di', 'finalita', 'creato_da')
        }),
        (_('Dati e Soggetti'), {
            'fields': ('categorie_dati', 'soggetti_interessati')
        }),
        (_('Flusso e Conservazione'), {
            'fields': ('destinatari_interni', 'destinatari_esterni', 'tempo_conservazione')
        }),
        (_('Rischio e Sicurezza'), {
            'fields': ('misure_sicurezza', 'livello_rischio', 'punteggio_rischio_calcolato', 'dpia_necessaria')
        }),
    )

# ==============================================================================
# 2. ADMIN PER GESTIONE DOCUMENTALE
# ==============================================================================

class VersioneDocumentoInline(admin.TabularInline):
    model = VersioneDocumento
    extra = 0
    fields = ('file', 'data_caricamento', 'caricato_da', 'note_versione')
    readonly_fields = ('data_caricamento', 'caricato_da')

@admin.register(DocumentoAziendale)
class DocumentoAziendaleAdmin(admin.ModelAdmin):
    list_display = ('nome', 'azienda', 'categoria', 'creato_da_template')
    list_filter = ('categoria', 'azienda')
    search_fields = ('nome',)
    inlines = [VersioneDocumentoInline]

# ==============================================================================
# 3. ADMIN PER AUDIT
# ==============================================================================

class AuditDomandaInline(admin.TabularInline):
    model = AuditDomanda
    extra = 1
    fields = ('testo', 'ordine')

@admin.register(AuditCategoria)
class AuditCategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ordine')
    inlines = [AuditDomandaInline]

@admin.register(AuditSession)
class AuditSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'azienda', 'data_creazione', 'completato')
    list_filter = ('completato', 'azienda')
    readonly_fields = ('data_creazione', 'creato_da')

# ==============================================================================
# 4. ADMIN PER INCIDENTI E RICHIESTE
# ==============================================================================

@admin.register(Incidente)
class IncidenteAdmin(admin.ModelAdmin):
    list_display = ('titolo', 'azienda', 'data_rilevamento', 'stato', 'notifica_garante_necessaria')
    list_filter = ('stato', 'notifica_garante_necessaria', 'azienda')
    search_fields = ('titolo', 'descrizione')

@admin.register(RichiestaInteressato)
class RichiestaInteressatoAdmin(admin.ModelAdmin):
    list_display = ('tipo_richiesta', 'richiedente_email', 'stato', 'data_ricezione', 'data_scadenza_risposta')
    list_filter = ('tipo_richiesta', 'stato', 'azienda')
    readonly_fields = ('data_ricezione',)

# ==============================================================================
# 5. ADMIN PER COMPITI, ASSET E SOFTWARE
# ==============================================================================

@admin.register(Compito)
class CompitoAdmin(admin.ModelAdmin):
    list_display = ('titolo', 'stato', 'priorita', 'data_scadenza', 'is_global')
    list_filter = ('stato', 'priorita', 'is_global', 'aziende_assegnate')
    filter_horizontal = ('aziende_assegnate',)

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('marca_modello', 'azienda', 'tipo_asset', 'utente_assegnatario', 'criticita', 'stato')
    list_filter = ('tipo_asset', 'criticita', 'stato', 'azienda')

@admin.register(Software)
class SoftwareAdmin(admin.ModelAdmin):
    list_display = ('nome_software', 'azienda', 'tipologia', 'locazione_server')
    list_filter = ('tipologia', 'azienda')

# ==============================================================================
# 6. ADMIN PER ORGANIGRAMMA PRIVACY
# ==============================================================================

@admin.register(RuoloPrivacy)
class RuoloPrivacyAdmin(admin.ModelAdmin):
    list_display = ('nome_cognome', 'ruolo_tipo', 'azienda')
    list_filter = ('ruolo_tipo', 'azienda')
    search_fields = ('nome_cognome', 'contatti')
    fieldsets = (
        (None, {'fields': ('azienda', 'ruolo_tipo', 'nome_cognome', 'contatti', 'atto_nomina')}),
    )

# ==============================================================================
# 7. ADMIN PER CSIRT (NIS2) e CONFIGURAZIONE RETE
# ==============================================================================

@admin.register(ReferenteCSIRT)
class ReferenteCSIRTAdmin(admin.ModelAdmin):
    list_display = ('azienda', 'ref_nome', 'ref_ruolo', 'data_nomina')
    search_fields = ('azienda__nome', 'ref_nome', 'ref_email')
    fieldsets = (
        (_('Dati Azienda'), {'fields': ('azienda', 'data_nomina')}),
        (_('Referente (Persona Fisica)'), {'fields': ('referente_user', 'ref_nome', 'ref_cognome', 'ref_cf', 'ref_email', 'ref_telefono', 'ref_ruolo', 'competenze_documentate', 'motivo_esterno')}),
        (_('Punto di Contatto (per Nomina)'), {'fields': ('pc_nome', 'pc_cognome', 'pc_email', 'codice_ipa')}),
        (_('Sostituti'), {'fields': ('sos1_nome', 'sos1_cognome', 'sos1_cf', 'sos1_email', 'sos2_nome', 'sos2_cognome', 'sos2_cf', 'sos2_email')}),
    )

@admin.register(NotificaIncidente)
class NotificaIncidenteAdmin(admin.ModelAdmin):
    list_display = ('titolo_incidente', 'azienda', 'stato', 'data_incidente', 'data_notifica')
    list_filter = ('stato', 'azienda')

@admin.register(ConfigurazioneRete)
class ConfigurazioneReteAdmin(admin.ModelAdmin):
    list_display = ('azienda', 'tipo_architettura', 'firewall_utilizzato', 'politica_patching')
    list_filter = ('tipo_architettura', 'politica_patching')
    search_fields = ('azienda__nome', 'firewall_utilizzato')

@admin.register(ComponenteRete)
class ComponenteReteAdmin(admin.ModelAdmin):
    list_display = ('nome_componente', 'tipo', 'criticita', 'configurazione')
    list_filter = ('tipo', 'criticita')

# ==============================================================================
# 8. SECURITY CHECKLIST BASE (MASTER DOMANDE)
# ==============================================================================

@admin.register(SecurityControl)
class SecurityControlAdmin(admin.ModelAdmin):
    list_display = ('control_id', 'area', 'descrizione', 'riferimento_iso')
    list_filter = ('area',)
    search_fields = ('control_id', 'descrizione', 'supporto_verifica', 'riferimento_iso')
    ordering = ('control_id',)
    
    fieldsets = (
        ('Identificazione', {
            'fields': ('control_id', 'area', 'riferimento_iso')
        }),
        ('Contenuto del Controllo', {
            'fields': ('descrizione', 'supporto_verifica')
        }),
    )

@admin.register(SecurityAudit)
class SecurityAuditAdmin(admin.ModelAdmin):
    list_display = ('id', 'azienda', 'data_creazione', 'completato', 'creato_da')
    list_filter = ('completato', 'azienda')

@admin.register(SecurityResponse)
class SecurityResponseAdmin(admin.ModelAdmin):
    list_display = ('audit', 'get_control_id', 'esito')
    list_filter = ('esito', 'audit__azienda')

    def get_control_id(self, obj):
        return obj.controllo.control_id
    get_control_id.short_description = 'ID Controllo'

# ==============================================================================
# 9. ADMIN PER AUDIT LOG (REGISTRO ACCESSI E AZIONI)
# ==============================================================================

@admin.register(AuditLog)
class AuditLogAdmin(ExportActionModelAdmin): # <--- Usiamo ExportActionModelAdmin invece di ImportExport
    resource_class = AuditLogResource
    
    list_display = ('data_ora', 'utente', 'azione', 'modello', 'indirizzo_ip')
    list_filter = ('azione', 'data_ora', 'utente')
    search_fields = ('utente__username', 'utente__email', 'descrizione')
    readonly_fields = ('data_ora', 'utente', 'azione', 'modello', 'descrizione', 'indirizzo_ip')
    
    # Questo aggiunge l'export anche nel menu a tendina "Azioni"
    actions = ['pulisci_log_vecchi']

    @admin.action(description='Cancella log selezionati più vecchi di 6 mesi')
    def pulisci_log_vecchi(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        sei_mesi_fa = timezone.now() - timedelta(days=180)
        vecchi = AuditLog.objects.filter(data_ora__lt=sei_mesi_fa)
        quantita = vecchi.count()
        vecchi.delete()
        self.message_user(request, f"Pulizia effettuata: rimossi {quantita} log obsoleti.")
@admin.register(Fornitore)
class FornitoreAdmin(admin.ModelAdmin):
    list_display = ('ragione_sociale', 'azienda_cliente', 'stato_valutazione', 'data_creazione')
    list_filter = ('stato_valutazione', 'azienda_cliente')
    search_fields = ('ragione_sociale', 'email_contatto')
    readonly_fields = ('access_token',) # Il token non va modificato a mano        