from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from colorfield.fields import ColorField 
from user_auth.models import CustomUser as User, Azienda, Consulente, Prodotto, AdminReferente, NotaAzienda 

# ==============================================================================
# FUNZIONI HELPER
# ==============================================================================
def upload_path_config(instance, filename):
    """Definisce il percorso di upload per i file di configurazione del sito."""
    return f'site_media/config/{filename}'

# ==============================================================================
# MODELLI CORSI
# ==============================================================================

class CategoriaCorso(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name=_("Nome Categoria"))
    def __str__(self): return self.nome
    class Meta: verbose_name_plural = _("Categorie Corso")

class Corso(models.Model):
    STATO_CHOICES = (('A', _('Attivo')), ('S', _('Sospeso')), ('F', _('Finito')))
    categoria = models.ForeignKey(CategoriaCorso, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Categoria"))
    nome = models.CharField(max_length=200, verbose_name=_("Titolo Corso"))
    descrizione = models.TextField(verbose_name=_("Descrizione Completa"))
    stato = models.CharField(max_length=1, choices=STATO_CHOICES, default='A', verbose_name=_("Stato"))
    durata_ore = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, verbose_name=_("Durata (Ore)"))
    is_obbligatorio = models.BooleanField(default=False, verbose_name=_("Obbligatorio per tutte le aziende"))
    def __str__(self): return self.nome
    class Meta: verbose_name_plural = _("Corsi"); ordering = ['nome'] 

class Modulo(models.Model):
    corso = models.ForeignKey(Corso, on_delete=models.CASCADE, related_name='moduli', verbose_name=_("Corso"))
    titolo = models.CharField(max_length=200, verbose_name=_("Titolo Modulo"))
    contenuto_html = models.TextField(blank=True, null=True, verbose_name=_("Contenuto HTML"))
    ordine = models.PositiveIntegerField(default=0, verbose_name=_("Ordine"))
    durata_minuti = models.PositiveIntegerField(default=30, verbose_name=_("Durata (Minuti)"))
    def __str__(self): return f"{self.corso.nome} - {self.titolo}"
    class Meta: verbose_name_plural = _("Moduli"); ordering = ['corso', 'ordine'] 

class Media(models.Model):
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE, related_name='media', verbose_name=_("Modulo"))
    nome = models.CharField(max_length=100, verbose_name=_("Nome File"))
    file = models.FileField(upload_to='corso_media/', verbose_name=_("File Media"))
    def __str__(self): return self.nome
    class Meta: verbose_name_plural = _("Media Moduli")

# ==============================================================================
# ISCRIZIONI E PROGRESSI
# ==============================================================================

class IscrizioneCorso(models.Model):
    studente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='iscrizioni', verbose_name=_("Studente"))
    corso = models.ForeignKey(Corso, on_delete=models.CASCADE, verbose_name=_("Corso"))
    data_iscrizione = models.DateTimeField(auto_now_add=True)
    completato = models.BooleanField(default=False)
    data_completamento = models.DateTimeField(null=True, blank=True)
    class Meta: unique_together = ('studente', 'corso'); verbose_name_plural = _("Iscrizioni Corso")

class ProgressoModulo(models.Model):
    iscrizione = models.ForeignKey(IscrizioneCorso, on_delete=models.CASCADE, related_name='progressi')
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE)
    completato = models.BooleanField(default=False)
    data_completamento = models.DateTimeField(null=True, blank=True)
    class Meta: unique_together = ('iscrizione', 'modulo'); verbose_name_plural = _("Progressi Moduli")

# ==============================================================================
# QUIZ E ATTESTATI
# ==============================================================================

class Quiz(models.Model):
    modulo = models.OneToOneField(Modulo, on_delete=models.CASCADE, related_name='quiz')
    titolo = models.CharField(max_length=100)
    punteggio_minimo = models.PositiveIntegerField(default=70, verbose_name=_("Punteggio Minimo (%)"))
    class Meta: verbose_name_plural = _("Quiz")

class Domanda(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='domande')
    testo = models.TextField(verbose_name=_("Testo Domanda"))
    ordine = models.PositiveIntegerField(default=0)
    class Meta: verbose_name_plural = _("Domande Quiz"); ordering = ['ordine']

class Risposta(models.Model):
    domanda = models.ForeignKey(Domanda, on_delete=models.CASCADE, related_name='risposte')
    testo = models.CharField(max_length=255, verbose_name=_("Testo Risposta"))
    is_corretta = models.BooleanField(default=False, verbose_name=_("È la risposta corretta?"))
    class Meta: verbose_name_plural = _("Risposte Quiz")

class Attestato(models.Model):
    iscrizione = models.OneToOneField(IscrizioneCorso, on_delete=models.CASCADE, related_name='attestato')
    codice_univoco = models.CharField(max_length=50, unique=True)
    data_rilascio = models.DateField(auto_now_add=True)
    class Meta: verbose_name_plural = _("Attestati")

# ==============================================================================
# IMPOSTAZIONI SITO (CONFIGURAZIONE NIS2 E SICUREZZA)
# ==============================================================================

class ImpostazioniSito(models.Model):
    nome_piattaforma = models.CharField(max_length=100, default="EasyGDPR", verbose_name=_("Nome Piattaforma"))
    colore_primario = models.CharField(max_length=7, default="#005a9c", verbose_name=_("Colore Principale (Esadecimale)"))
    
    colore_secondario = ColorField(
        default='#F8F9FA', 
        max_length=18, 
        verbose_name=_("Colore Secondario"), 
        help_text=_("Usato per elementi secondari o highlight del tema.")
    )
    
    logo_principale = models.ImageField(upload_to=upload_path_config, blank=True, null=True, verbose_name=_("Logo Piattaforma")) 
    
    # === CAMPI EMAILJS ===
    email_service_id = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Email Service ID"))
    email_public_key = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Email Public Key"))
    email_private_key = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Email Private Key"))
    email_template_id = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Email Template ID (Benvenuto)"))
    email_reset_template_id = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Email Reset Template ID"))
    email_scadenza_template_id = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Email Scadenza Template ID"))
    email_scadenza_compito_id = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Email Scadenza Compito ID"))
    
    # === CAMPO AI ===
    gemini_api_key = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Chiave API Google Gemini"))
    # CAMPI DEASHED 
    dehashed_email = models.EmailField(max_length=255, blank=True, null=True)
    dehashed_api_key = models.CharField(max_length=255, blank=True, null=True)
    # === CONFIGURAZIONE NESSUS (NIS2 Art. 21) ===
    nessus_url = models.URLField(
        max_length=255, 
        default="https://localhost:8834",
        verbose_name=_("URL Server Nessus"),
        help_text=_("Indirizzo del server Nessus per la scansione asset.")
    )
    nessus_access_key = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name=_("Nessus Access Key"),
        help_text=_("Chiave di accesso generata in Nessus (Settings -> My Account -> API Keys).")
    )
    nessus_secret_key = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name=_("Nessus Secret Key"),
        help_text=_("Chiave segreta generata in Nessus.")
    )
    # === CONFIGURAZIONE PENTEST-TOOLS ===
    pentest_tools_api_key = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name=_("Pentest-Tools API Key"),
        help_text=_("Chiave API recuperata dal profilo di Pentest-Tools.")
    )
    pentest_tools_api_url = models.URLField(
        max_length=255, 
        default="https://api.pentest-tools.com/v2",
        verbose_name=_("URL API Pentest-Tools"),
        help_text=_("URL base per le chiamate API (default v2).")
    )
    # === CONFIGURAZIONE VIEWDNS ===
    viewdns_api_key = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name=_("ViewDNS API Key"),
        help_text=_("Chiave API per i servizi di ViewDNS.info")
    )

    # === TEMPLATE CSIRT ===
    template_nomina_csirt = models.FileField(
        upload_to=upload_path_config, 
        blank=True, 
        null=True, 
        verbose_name=_("Template Word Nomina CSIRT"),
        help_text=_("Carica qui il file .docx con i segnaposto.")
    )

    def save(self, *args, **kwargs):
        self.pk = 1 
        super().save(*args, **kwargs)

    def __str__(self): return "Impostazioni Generali" 
    class Meta: 
        verbose_name = _("Impostazioni Sito")
        verbose_name_plural = _("Impostazioni Sito")