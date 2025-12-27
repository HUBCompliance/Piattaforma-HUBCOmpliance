from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from user_auth.models import CustomUser as User, Azienda, Consulente

# ==============================================================================
# 0. PARAMETRI MONITORAGGIO TECNICO (NIS2)
# ==============================================================================
class ParametriMonitoraggio(models.Model):
    azienda = models.OneToOneField(Azienda, on_delete=models.CASCADE, related_name='monitoraggio_tecnico')
    dominio_web = models.CharField(max_length=255, blank=True, help_text=_("Es: ferrari.it"))
    prometheus_url = models.URLField(default="http://localhost:9090")
    mod_monitoring_attivo = models.BooleanField(default=False)
    def __str__(self): return f"Parametri NIS2 - {self.azienda.nome}"

# ==============================================================================
# 1. MODELLI BASE E TRATTAMENTI (BONIFICATO)
# ==============================================================================
class CategoriaDati(models.Model):
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome

class SoggettoInteressato(models.Model):
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome

class Trattamento(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    nome_trattamento = models.CharField(max_length=200)
    tipo_ruolo = models.CharField(max_length=20, choices=[('TITOLARE', 'Titolare'), ('RESPONSABILE', 'Responsabile')], default='TITOLARE')
    per_conto_di = models.CharField(max_length=200, blank=True, null=True)
    finalita = models.TextField()
    categorie_dati = models.ManyToManyField(CategoriaDati)
    soggetti_interessati = models.ManyToManyField(SoggettoInteressato)
    destinatari_interni = models.TextField(blank=True, null=True)
    destinatari_esterni = models.TextField(blank=True, null=True)
    tempo_conservazione = models.CharField(max_length=200)
    misure_sicurezza = models.TextField()
    livello_rischio = models.CharField(max_length=20, default='BASSO')
    punteggio_rischio_calcolato = models.IntegerField(default=0)
    dpia_necessaria = models.BooleanField(default=False)
    creato_da = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self): return self.nome_trattamento

class DomandaChecklist(models.Model):
    testo = models.TextField()
    punteggio_rischio = models.IntegerField(default=1)
    ordine = models.IntegerField(default=0)
    def __str__(self): return self.testo

class RispostaChecklist(models.Model):
    """ RISOLVE IMPORT ERROR: Necessario per l'analisi dei rischi e accountability """
    trattamento = models.ForeignKey(Trattamento, on_delete=models.CASCADE, related_name='risposte_checklist')
    domanda = models.ForeignKey(DomandaChecklist, on_delete=models.CASCADE)
    risposta = models.BooleanField(default=False) # True = Rischio identificato
    note = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Risposta Checklist")
        verbose_name_plural = _("Risposte Checklist")

# ==============================================================================
# 2. GESTIONE DOCUMENTALE
# ==============================================================================
class CategoriaDocumento(models.Model):
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome

class TemplateDocumento(models.Model):
    categoria = models.ForeignKey(CategoriaDocumento, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    descrizione = models.TextField(blank=True)
    file = models.FileField(upload_to='templates_docs/')
    def __str__(self): return self.nome

class DocumentoAziendale(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    categoria = models.ForeignKey(CategoriaDocumento, on_delete=models.SET_NULL, null=True)
    nome = models.CharField(max_length=200)
    creato_da_template = models.ForeignKey(TemplateDocumento, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self): return self.nome

class VersioneDocumento(models.Model):
    documento = models.ForeignKey(DocumentoAziendale, on_delete=models.CASCADE, related_name='versioni')
    file = models.FileField(upload_to='documenti_aziendali/')
    data_caricamento = models.DateTimeField(auto_now_add=True)
    caricato_da = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    note_versione = models.CharField(max_length=200, blank=True)

# ==============================================================================
# 3. AUDIT E SESSIONI (RISOLVE TYPEERROR)
# ==============================================================================
class AuditCategoria(models.Model):
    nome = models.CharField(max_length=100)
    ordine = models.IntegerField(default=0)
    def __str__(self): return self.nome

class AuditDomanda(models.Model):
    categoria = models.ForeignKey(AuditCategoria, on_delete=models.CASCADE, related_name='domande')
    testo = models.TextField()
    ordine = models.IntegerField(default=0)
    def __str__(self): return self.testo

class AuditSession(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    titolo = models.CharField(max_length=255, default=_("Audit Session"))
    data_creazione = models.DateTimeField(auto_now_add=True)
    creato_da = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    completato = models.BooleanField(default=False)
    stato = models.CharField(max_length=20, default='APERTO') # Richiesto dalla View
    note = models.TextField(blank=True)
    def __str__(self): return f"{self.titolo} - {self.azienda.nome}"

class AuditRisposta(models.Model):
    sessione = models.ForeignKey(AuditSession, on_delete=models.CASCADE, related_name='risposte')
    domanda = models.ForeignKey(AuditDomanda, on_delete=models.CASCADE)
    risposta = models.BooleanField(default=False)
    note = models.TextField(blank=True)
    class Meta: unique_together = ('sessione', 'domanda')

# ==============================================================================
# 4. INCIDENTI E RICHIESTE
# ==============================================================================
class Incidente(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    data_rilevamento = models.DateTimeField(default=timezone.now)
    titolo = models.CharField(max_length=200)
    descrizione = models.TextField()
    stato = models.CharField(max_length=20, choices=(('APERTO', 'Aperto'), ('GESTIONE', 'In Gestione'), ('CHIUSO', 'Chiuso')), default='APERTO')
    notifica_garante_necessaria = models.BooleanField(default=False)
    valutazione_rischio = models.TextField(blank=True)
    def __str__(self): return self.titolo

class RichiestaInteressato(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    data_ricezione = models.DateTimeField(auto_now_add=True)
    tipo_richiesta = models.CharField(max_length=20, default='ACCESSO')
    richiedente_email = models.EmailField()
    richiedente_nome = models.CharField(max_length=200)
    richiesta_testo = models.TextField()
    stato = models.CharField(max_length=20, default='RICEVUTA')
    data_scadenza_risposta = models.DateField(null=True, blank=True)

# ==============================================================================
# 5. COMPITI, ASSET E SOFTWARE
# ==============================================================================
# ==============================================================================
# COMPITI / TASK (VERSIONE COMPLETA PER FORMS E NIS2)
# ==============================================================================
# ==============================================================================
# COMPITI / TASK (VERSIONE BONIFICATA)
# ==============================================================================
class Compito(models.Model):
    STATO_CHOICES = (('APERTO', 'Aperto'), ('IN_CORSO', 'In Corso'), ('COMPLETATO', 'Completato'))
    PRIORITA_CHOICES = (('BASSA', 'Bassa'), ('MEDIA', 'Media'), ('ALTA', 'Alta'))

    titolo = models.CharField(max_length=200, verbose_name=_("Titolo Attività"))
    descrizione = models.TextField(blank=True, verbose_name=_("Descrizione/Dettaglio")) # RISOLVE IL FIELDERROR
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE, null=True, blank=True)
    aziende_assegnate = models.ManyToManyField(Azienda, blank=True, related_name='compiti_molteplici')

    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='APERTO')
    priorita = models.CharField(max_length=10, choices=PRIORITA_CHOICES, default='MEDIA')
    data_scadenza = models.DateField(null=True, blank=True)
    is_global = models.BooleanField(default=False)

    data_creazione = models.DateTimeField(auto_now_add=True)
    creato_da = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = _("Compito")
        verbose_name_plural = _("Compiti")

    def __str__(self):
        return self.titolo

class Asset(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    tipo_asset = models.CharField(max_length=50, default='PC')
    marca_modello = models.CharField(max_length=100)
    utente_assegnatario = models.CharField(max_length=100, blank=True)
    criticita = models.CharField(max_length=20, default='MEDIA')
    stato = models.CharField(max_length=20, default='IN_USO')

class Software(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    nome_software = models.CharField(max_length=100)
    tipologia = models.CharField(max_length=20, default='LOCALE')
    locazione_server = models.CharField(max_length=100, blank=True)

# ==============================================================================
# 6. ORGANIGRAMMA E TIA
# ==============================================================================
class RuoloPrivacy(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    ruolo_tipo = models.CharField(max_length=30)
    nome_cognome = models.CharField(max_length=100)
    contatti = models.CharField(max_length=200, blank=True)
    atto_nomina = models.FileField(upload_to='nomine/', blank=True, null=True)

class Paese(models.Model):
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome

class ValutazioneTIA(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    paese_destinazione = models.ForeignKey(Paese, on_delete=models.CASCADE)

class Videosorveglianza(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    nome_impianto = models.CharField(max_length=100)

# ==============================================================================
# 7. CSIRT (NIS2) E RETE
# ==============================================================================
class ReferenteCSIRT(models.Model):
    azienda = models.OneToOneField(Azienda, on_delete=models.CASCADE, related_name='ref_csirt_final')
    data_nomina = models.DateField(default=timezone.now)
    referente_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ref_nome = models.CharField(max_length=100, blank=True)
    ref_cognome = models.CharField(max_length=100, blank=True)
    ref_cf = models.CharField(max_length=16, blank=True)
    ref_email = models.EmailField(blank=True)
    ref_telefono = models.CharField(max_length=20, blank=True)
    ref_ruolo = models.CharField(max_length=100, blank=True)
    competenze_documentate = models.BooleanField(default=False)
    motivo_esterno = models.TextField(blank=True)
    pc_nome = models.CharField(max_length=100, blank=True)
    pc_cognome = models.CharField(max_length=100, blank=True)
    pc_email = models.EmailField(blank=True)
    codice_ipa = models.CharField(max_length=100, blank=True)
    sos1_nome = models.CharField(max_length=100, blank=True)
    sos1_cognome = models.CharField(max_length=100, blank=True)
    sos1_cf = models.CharField(max_length=16, blank=True)
    sos1_email = models.EmailField(blank=True)
    sos2_nome = models.CharField(max_length=100, blank=True)
    sos2_cognome = models.CharField(max_length=100, blank=True)
    sos2_cf = models.CharField(max_length=16, blank=True)
    sos2_email = models.EmailField(blank=True)

class NotificaIncidente(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE, related_name='notifiche_nis2_final')
    titolo_incidente = models.CharField(max_length=255)
    data_incidente = models.DateTimeField()
    data_notifica = models.DateTimeField(null=True, blank=True)
    stato = models.CharField(max_length=20, default='APERTA')

class ConfigurazioneRete(models.Model):
    azienda = models.OneToOneField(Azienda, on_delete=models.CASCADE)
    tipo_architettura = models.CharField(max_length=50, default='HIERARCHICAL')
    firewall_utilizzato = models.CharField(max_length=100, blank=True)
    politica_patching = models.CharField(max_length=50, default='MANUALE')

class ComponenteRete(models.Model):
    configurazione = models.ForeignKey(ConfigurazioneRete, on_delete=models.CASCADE, related_name='componenti_final')
    nome_componente = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50, default='DEVICE')
    criticita = models.CharField(max_length=20, default='MEDIA')
