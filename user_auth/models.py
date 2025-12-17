from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

# ==============================================================================
# 0. FUNZIONI HELPER PER IL CARICAMENTO FILE (Risoluzione Attribute Error)
# ==============================================================================

def upload_path_azienda_logo(instance, filename):
    """Definisce il percorso di caricamento per il logo dell'azienda (usato nelle vecchie migrazioni)."""
    # Questo è un percorso generico per il logo principale
    return f'aziende/{instance.pk}/logos/principale/{filename}'

def upload_path_azienda_attestato(instance, filename):
    """Definisce il percorso di caricamento per il logo dell'attestato (Risolve l'AttributeError)."""
    return f'aziende/{instance.pk}/logos/attestato/{filename}'

# ==============================================================================
# 1. MODELLO PRODOTTO
# ==============================================================================

class Prodotto(models.Model):
    """Rappresenta un servizio, un corso o un prodotto vendibile sulla piattaforma."""
    nome = models.CharField(max_length=255, unique=True, verbose_name=_("Nome Prodotto"))
    descrizione = models.TextField(blank=True, verbose_name=_("Descrizione"))
    prezzo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Prodotto")
        verbose_name_plural = _("Prodotti")

    def __str__(self):
        return self.nome


# ==============================================================================
# 2. MODELLO AZIENDA (Con manager_users e flag moduli)
# ==============================================================================

class Azienda(models.Model):
    nome = models.CharField(max_length=255, verbose_name=_("Nome Azienda"))
    p_iva = models.CharField(max_length=20, unique=False, verbose_name=_("P.IVA/Cod. Fisc."))
    indirizzo = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Indirizzo Sede"))
    
    # Campi di configurazione moduli (gestiti dal Consulente)
    mod_cruscotto = models.BooleanField(default=True, verbose_name=_("Attiva Cruscotto principale"))
    mod_trattamenti = models.BooleanField(default=True, verbose_name=_("Attiva Registro Trattamenti"))
    mod_documenti = models.BooleanField(default=True, verbose_name=_("Attiva Gestione Documenti"))
    mod_audit = models.BooleanField(default=True, verbose_name=_("Attiva Audit Compliance"))
    mod_incidenti = models.BooleanField(default=True, verbose_name=_("Attiva Segnalazione Incidenti"))
    mod_richieste = models.BooleanField(default=True, verbose_name=_("Attiva Richieste Interessati"))
    mod_formazione = models.BooleanField(default=True, verbose_name=_("Attiva Gestione Formazione"))
    mod_storico_audit = models.BooleanField(default=True, verbose_name=_("Attiva Storico Sessioni Audit"))
    mod_videosorveglianza = models.BooleanField(default=False, verbose_name=_("Attiva Videosorveglianza"))
    mod_tia = models.BooleanField(default=False, verbose_name=_("Attiva TIA Estero"))
    mod_organigramma = models.BooleanField(default=False, verbose_name=_("Attiva Organigramma Privacy"))
    mod_csirt = models.BooleanField(default=False, verbose_name=_("Attiva Gestione CSIRT (NIS2)"))
    
    # Campi Logo (Mantenuti per compatibilità con le vecchie migrazioni)
    logo_principale = models.ImageField(upload_to=upload_path_azienda_logo, blank=True, null=True, verbose_name=_("Logo Principale"))
    logo_attestato = models.ImageField(upload_to=upload_path_azienda_attestato, blank=True, null=True, verbose_name=_("Logo Attestato"))
    
    # AZIONE FORTE: Relazione di gestione diretta (risolve il problema Consulente)
    manager_users = models.ManyToManyField(
        'user_auth.CustomUser', 
        related_name='aziende_gestite_direttamente', 
        blank=True,
        verbose_name=_("Manager (Utenti Consulenti)")
    )
    
    data_creazione = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = _("Aziende")

    def __str__(self):
        return self.nome
        
# ==============================================================================
# 3. MODELLO CUSTOMUSER (Utenti con Ruoli)
# ==============================================================================

class CustomUser(AbstractUser):
    RUOLI_CHOICES = (
        ('ADMIN', 'Amministratore di Sistema'),
        ('CONSULENTE', 'Consulente / DPO Esterno'),
        ('REFERENTE', 'Referente Privacy Aziendale'),
        ('STUDENTE', 'Dipendente / Utente E-learning'),
    )
    ruolo = models.CharField(max_length=20, choices=RUOLI_CHOICES, default='STUDENTE', verbose_name=_("Ruolo Utente"))
    
    # Associazione all'Azienda (per REFERENTE e STUDENTE). Null per ADMIN e CONSULENTE.
    azienda = models.ForeignKey(
        Azienda, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='utenti_aziendali',
        verbose_name=_("Azienda Associata")
    )
    
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Telefono"))
    data_nascita = models.DateField(blank=True, null=True, verbose_name=_("Data di Nascita"))
    
    is_dpo = models.BooleanField(default=False, verbose_name=_("Designato come DPO"))

    class Meta:
        verbose_name = _("Utente")
        verbose_name_plural = _("Utenti")

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_ruolo_display()})"
        
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

# ==============================================================================
# 4. MODELLO CONSULENTE
# ==============================================================================

class Consulente(models.Model):
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        limit_choices_to={'ruolo': 'CONSULENTE'},
        primary_key=True
    )
    
    codice_albo = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Codice Albo Professionale"))
    
    class Meta:
        verbose_name = _("Consulente")
        verbose_name_plural = _("Consulenti")
        
    def __str__(self):
        return f"Profilo Consulente: {self.user.get_full_name()}"

# ==============================================================================
# 5. MODELLI AGGIUNTIVI (Per completezza di importazione)
# ==============================================================================

class AdminReferente(models.Model):
    # Modello di placeholder per la classe AdminReferente
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = _("Admin Referente")
        
    def __str__(self):
        return f"Admin Referente: {self.user.username}"
    class Meta:
        verbose_name = _("Referente ADMIN")
        verbose_name_plural = _("Referenti ADMIN")
        
class NotaAzienda(models.Model):
    # Modello di placeholder per la classe NotaAzienda
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    testo = models.TextField()
    data_creazione = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Nota Aziendale")
        verbose_name_plural = _("Note Aziendali")

    def __str__(self):
        return f"Nota per {self.azienda.nome}"