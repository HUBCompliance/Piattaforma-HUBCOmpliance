import requests
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

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

def build_password_action_url(user, request=None):
    """Costruisce l'URL per impostare/reimpostare la password dell'utente."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    if request:
        current_site = get_current_site(request)
        protocol = 'https' if request.is_secure() else 'http'
        domain = f"{protocol}://{current_site.domain}"
    else:
        domain = getattr(settings, 'DEFAULT_DOMAIN', 'http://127.0.0.1:8000')

    return f"{domain}/reset/{uid}/{token}/"


def send_password_creation_email(user, action_url, config):
    """Invia l'email con il link per impostare la password tramite EmailJS."""
    template_params = {
        "to_email": user.email,
        "user_name": f"{user.first_name} {user.last_name}" if user.first_name else user.username,
        "ruolo": user.ruolo,
        "azienda_nome": user.azienda.nome if user.azienda else "Non specificata",
        "data_invio": timezone.now().strftime("%d/%m/%Y"),
        "action_url": action_url,
    }

    payload = {
        "service_id": config.email_service_id,
        "template_id": config.email_template_id,
        "user_id": config.email_public_key,
        "accessToken": config.email_private_key,
        "template_params": template_params,
    }

    response = requests.post(
        "https://api.emailjs.com/api/v1.0/email/send",
        json=payload,
        timeout=10,
    )

    if response.status_code == 200:
        print(f"✅ Email di attivazione inviata a: {user.email}")
    else:
        print(f"❌ Errore EmailJS: {response.text}")


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
        """
        Eseguito dopo la creazione dell'utente. Genera il link monouso 
        e invia la mail tramite EmailJS.
        """
        instance = row_result.instance
        
        if instance and instance.email:
            try:
                config = ImpostazioniSito.objects.first()
                if not config or not config.email_service_id:
                    print("⚠️ Configurazione EmailJS non trovata in Impostazioni Sito.")
                    return

                if not instance.password:
                    instance.set_unusable_password()
                    instance.save()

                action_url = build_password_action_url(instance)
                print(f"DEBUG - Link generato per {instance.username}: {action_url}")
                send_password_creation_email(instance, action_url, config)

            except Exception as e:
                print(f"⚠️ Errore critico dopo importazione riga: {e}")

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
        ('Dettagli Azienda', {'fields': ('nome', 'p_iva', 'indirizzo')}),
        ('Branding Aziendale', {'fields': ('logo_principale', 'logo_attestato')}),
        ('Gestione e Stato', {'fields': ('is_active', 'manager_users')}),
        ('Configurazione Moduli Attivi', {
            'fields': (
                ('mod_cruscotto', 'mod_storico_audit'),
                ('mod_trattamenti', 'mod_documenti', 'mod_audit'), 
                ('mod_videosorveglianza', 'mod_tia', 'mod_organigramma'),
                ('mod_csirt', 'mod_incidenti', 'mod_richieste', 'mod_formazione'),
            )
        }),
    )

# ==============================================================================
# 2. ALTRI MODELLI
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

# ==============================================================================
# 3. ADMIN PER IL MODELLO USER (Import/Export)
# ==============================================================================

class CustomUserAdmin(BaseUserAdmin, ImportExportActionModelAdmin):
    resource_class = UserResource
    
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Ruoli e Associazione Azienda'), {'fields': ('ruolo', 'azienda', 'is_dpo')}),
    )
    list_display = BaseUserAdmin.list_display + ('ruolo', 'azienda')
    list_filter = BaseUserAdmin.list_filter + ('ruolo', 'azienda')

    def save_model(self, request, obj, form, change):
        is_new = not change

        if is_new and not obj.password:
            obj.set_unusable_password()

        super().save_model(request, obj, form, change)

        if is_new and obj.email:
            try:
                config = ImpostazioniSito.objects.first()
                if not config or not config.email_service_id:
                    print("⚠️ Configurazione EmailJS non trovata in Impostazioni Sito.")
                    return

                action_url = build_password_action_url(obj, request=request)
                send_password_creation_email(obj, action_url, config)
            except Exception as e:
                print(f"⚠️ Errore invio email dopo creazione utente singolo: {e}")

# Registrazione dell'utente
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

admin.site.register(User, CustomUserAdmin)

if 'AdminReferente' in globals():
    @admin.register(AdminReferente)
    class AdminReferenteAdmin(admin.ModelAdmin):
        list_display = ('user',)