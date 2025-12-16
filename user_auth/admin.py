from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser as User, Azienda, Consulente, Prodotto, AdminReferente, NotaAzienda
from .forms import ReferenteStudenteForm # Importiamo i form se necessario
from django.utils.translation import gettext_lazy as _


# ==============================================================================
# 1. ADMIN PER IL MODELLO AZIENDA (Correzione di E108, E116)
# ==============================================================================

@admin.register(Azienda)
class AziendaAdmin(admin.ModelAdmin):
    # E108/E116: Correzione dei campi list_display e list_filter
    list_display = (
        'nome', 
        'p_iva',  # Corretto da 'partita_iva' a 'p_iva'
        'is_active', 
        'data_creazione'
        # I campi di contratto ('stato_contratto', 'data_scadenza_contratto') sono stati rimossi o non esistono
    )
    
    list_filter = (
        'is_active', 
        'data_creazione',
        # Rimosso il filtro per 'stato_contratto'
    )
    
    search_fields = ('nome', 'p_iva')
    
    # === AGGIUNTA: Gestione del campo M2M manager_users ===
    filter_horizontal = ('manager_users',) # E019: Correzione: manager_users è l'unico M2M
    
    fieldsets = (
        ('Dettagli Azienda', {
            'fields': ('nome', 'p_iva', 'indirizzo')
        }),
        ('Gestione e Stato', {
            'fields': ('is_active', 'manager_users')
        }),
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
# 2. ADMIN PER IL MODELLO CONSULENTE (Correzione di E019, E108)
# ==============================================================================

@admin.register(Consulente)
class ConsulenteAdmin(admin.ModelAdmin):
    # E108: Correzione: il campo 'telefono' non è direttamente su Consulente, ma su User
    list_display = (
        'user', 
        # Rimosso 'telefono' che è un campo su CustomUser
    )
    
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    
    # E019: Rimosso 'aziende_gestite' da filter_horizontal perché non è un campo su questo modello
    # La gestione delle aziende avviene tramite AziendaAdmin.
    # filter_horizontal = ('aziende_gestite',) <-- Rimosso

# ==============================================================================
# 3. ADMIN PER IL MODELLO NOTAAZIENDA (Correzione di E035, E108)
# ==============================================================================

@admin.register(NotaAzienda)
class NotaAziendaAdmin(admin.ModelAdmin):
    # E108: Corretto list_display per usare i campi esistenti (assumo 'data_creazione' e 'testo')
    list_display = (
        'azienda', 
        'testo', # 'creata_da' è stato rimosso o non è un campo su NotaAzienda
        'data_creazione' 
    )
    
    # E035: Corretto readonly_fields per usare i campi esistenti
    readonly_fields = ('data_creazione',) # 'creata_da' è stato rimosso o non esiste
    
    list_filter = ('azienda',)

# ==============================================================================
# 4. ADMIN PER IL MODELLO USER e PRODOTTO
# ==============================================================================

class CustomUserAdmin(BaseUserAdmin):
    # Aggiungi 'ruolo' e 'azienda' ai campi utente
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Ruoli e Associazione Azienda'), {'fields': ('ruolo', 'azienda', 'is_dpo')}),
    )
    list_display = BaseUserAdmin.list_display + ('ruolo', 'azienda')
    list_filter = BaseUserAdmin.list_filter + ('ruolo', 'azienda')

admin.site.register(User, CustomUserAdmin)

@admin.register(Prodotto)
class ProdottoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'prezzo', 'is_active')
    list_filter = ('is_active',)

# Placeholder per AdminReferente (se necessario)
if 'AdminReferente' in globals():
    @admin.register(AdminReferente)
    class AdminReferenteAdmin(admin.ModelAdmin):
        list_display = ('user',)