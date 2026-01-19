import requests
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse

# Strumenti per il Link Monouso di Sicurezza
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

# Import dai modelli
from .models import CustomUser as User, Azienda, Consulente, Prodotto, AdminReferente, NotaAzienda
from courses.models import ImpostazioniSito

# Import per Excel
from import_export import resources, fields
from import_export.admin import ImportExportActionModelAdmin
from import_export.widgets import ForeignKeyWidget

# ==============================================================================
# 0. RISORSA PER IMPORTAZIONE UTENTI (Excel + EmailJS Dinamico)
# ==============================================================================

class UserResource(resources.ModelResource):
    azienda = fields.Field(
        column_name='azienda',
        attribute='azienda',
        widget=ForeignKeyWidget(Azienda, 'nome')
    )

    class Meta:
        model = User
        import_id_fields = ('username',)
        fields = ('username', 'email', 'first_name', 'last_name', 'ruolo', 'azienda')
        skip_unchanged = True
        report_skipped = True

    def after_import_row(self, row, row_result, **kwargs):
        instance = row_result.instance
        if instance and instance.email:
             from .views import trigger_set_password_email
             # Invia la mail di benvenuto/set password dopo l'importazione
             trigger_set_password_email(None, instance)
             print(f"✅ Email inviata per {instance.email}")

# ==============================================================================
# 1. ADMIN PER IL MODELLO AZIENDA
# ==============================================================================

@admin.register(Azienda)
class AziendaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'p_iva', 'is_active', 'data_creazione')
    list_filter = ('is_active', 'data_creazione')
    search_fields = ('nome', 'p_iva')
    filter_horizontal = ('manager_users',)

    fieldsets = (
        ('Dettagli Azienda', {'fields': ('nome', 'p_iva', 'indirizzo', 'logo_principale', 'logo_attestato')}),
        ('Gestione e Stato', {'fields': ('is_active', 'manager_users')}),
        ('Configurazione Moduli Attivi', {
            'fields': (
                ('mod_cruscotto', 'mod_storico_audit'),
                ('mod_trattamenti', 'mod_documenti', 'mod_audit'),
                ('mod_videosorveglianza', 'mod_tia', 'mod_organigramma'),
                ('mod_csirt', 'mod_incidenti', 'mod_richieste', 'mod_formazione'),
                ('mod_asset', 'mod_analisi_rischi', 'mod_rete'),
                ('mod_fornitori', 'mod_whistleblowing'),
            )
        }),
    )

# ==============================================================================
# 2. ALTRI MODELLI ANAGRAFICI
# ==============================================================================

@admin.register(Consulente)
class ConsulenteAdmin(admin.ModelAdmin):
    list_display = ('user',)

@admin.register(NotaAzienda)
class NotaAziendaAdmin(admin.ModelAdmin):
    list_display = ('azienda', 'testo', 'data_creazione')
    readonly_fields = ('data_creazione',)

@admin.register(Prodotto)
class ProdottoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'prezzo', 'is_active')

if 'AdminReferente' in globals():
    @admin.register(AdminReferente)
    class AdminReferenteAdmin(admin.ModelAdmin):
        list_display = ('user',)

# ==============================================================================
# 3. ADMIN PER IL MODELLO USER (CustomUser con Import/Export)
# ==============================================================================

class CustomUserAdmin(BaseUserAdmin, ImportExportActionModelAdmin):
    resource_class = UserResource

    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Ruoli e Associazione Azienda'), {'fields': ('ruolo', 'azienda', 'is_dpo')}),
    )
    list_display = BaseUserAdmin.list_display + ('ruolo', 'azienda')
    list_filter = BaseUserAdmin.list_filter + ('ruolo', 'azienda')

# Registrazione sicura del modello User
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

admin.site.register(User, CustomUserAdmin)

# NOTA: Il modello AuditLog è stato spostato in compliance/admin.py 
# per mantenere la logica di business separata dall'anagrafica utenti.
