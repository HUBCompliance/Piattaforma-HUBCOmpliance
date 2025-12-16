from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
# Assicurati che i tuoi modelli siano importati correttamente
from user_auth.models import CustomUser as User, Azienda, Consulente 

# ==============================================================================
# MODELLI BASE (Categorie, Soggetti)
# ==============================================================================

class CategoriaDati(models.Model):
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome

class SoggettoInteressato(models.Model):
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome

# ==============================================================================
# 1. REGISTRO TRATTAMENTI
# ==============================================================================

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
    trattamento = models.ForeignKey(Trattamento, on_delete=models.CASCADE, related_name='risposte_checklist')
    domanda = models.ForeignKey(DomandaChecklist, on_delete=models.CASCADE)
    risposta = models.BooleanField(default=False) # True = Sì (Rischio presente)

# ==============================================================================
# 2. GESTIONE DOCUMENTALE
# ==============================================================================

class CategoriaDocumento(models.Model):
    """Serve unicamente per categorizzare i Documenti Aziendali."""
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
# 3. INCIDENTI (DATA BREACH)
# ==============================================================================

class Incidente(models.Model):
    STATO_CHOICES = (('APERTO', 'Aperto'), ('GESTIONE', 'In Gestione'), ('CHIUSO', 'Chiuso'))
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    data_rilevamento = models.DateTimeField()
    titolo = models.CharField(max_length=200)
    descrizione = models.TextField()
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='APERTO')
    valutazione_rischio = models.TextField(blank=True)
    notifica_garante_necessaria = models.BooleanField(default=False)
    notifica_interessati_necessaria = models.BooleanField(default=False)
    data_scadenza_notifica = models.DateTimeField(null=True, blank=True)
    azioni_correttive = models.TextField(blank=True)
    segnalato_da = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

# ==============================================================================
# 4. RICHIESTE INTERESSATI
# ==============================================================================

class RichiestaInteressato(models.Model):
    TIPO_CHOICES = (('ACCESSO', 'Accesso'), ('RETTIFICA', 'Rettifica'), ('CANCELLAZIONE', 'Cancellazione'), ('OPPOSIZIONE', 'Opposizione'), ('PORTABILITA', 'Portabilità'))
    STATO_CHOICES = (('RICEVUTA', 'Ricevuta'), ('IN_LAVORAZIONE', 'In Lavorazione'), ('EVASA', 'Evasa'), ('RIFIUTATA', 'Rifiutata'))
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    data_ricezione = models.DateTimeField(auto_now_add=True)
    tipo_richiesta = models.CharField(max_length=20, choices=TIPO_CHOICES)
    richiedente_nome = models.CharField(max_length=200)
    richiedente_email = models.EmailField()
    richiesta_testo = models.TextField()
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='RICEVUTA')
    note_interne = models.TextField(blank=True)
    data_scadenza_risposta = models.DateField(null=True, blank=True)
    gestita_da = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

# ==============================================================================
# 5. AUDIT
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
    data_creazione = models.DateTimeField(auto_now_add=True)
    creato_da = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    completato = models.BooleanField(default=False)
    note = models.TextField(blank=True)

class AuditRisposta(models.Model):
    sessione = models.ForeignKey(AuditSession, on_delete=models.CASCADE, related_name='risposte')
    domanda = models.ForeignKey(AuditDomanda, on_delete=models.CASCADE)
    risposta = models.BooleanField(default=False) # Sì/No
    note = models.TextField(blank=True)
    class Meta: unique_together = ('sessione', 'domanda')

# ==============================================================================
# 6. COMPITI
# ==============================================================================

class Compito(models.Model):
    STATO_CHOICES = (('APERTO', 'Aperto'), ('IN_CORSO', 'In Corso'), ('COMPLETATO', 'Completato'))
    PRIORITA_CHOICES = (('BASSA', 'Bassa'), ('MEDIA', 'Media'), ('ALTA', 'Alta'))
    creato_da = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compiti_creati')
    aziende_assegnate = models.ManyToManyField(Azienda, blank=True) 
    is_global = models.BooleanField(default=False) 
    titolo = models.CharField(max_length=200)
    descrizione = models.TextField(blank=True)
    data_scadenza = models.DateField(null=True, blank=True)
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='APERTO')
    priorita = models.CharField(max_length=10, choices=PRIORITA_CHOICES, default='MEDIA')
    def __str__(self): return self.titolo

# ==============================================================================
# NUOVO MODULO: CONFIGURAZIONE DI RETE INFORMATICA (PADRE)
# ==============================================================================

class ConfigurazioneRete(models.Model):
    """ Modello per la configurazione di rete principale. """
    ARCHITETTURA_CHOICES = [
        ('STAR', 'Star'), 
        ('MESH', 'Mesh'), 
        ('HIERARCHICAL', 'Gerarchica'), 
        ('FLAT', 'Piatta')
    ]
    VPN_CHOICES = [
        ('AZIENDA', 'Gestita Internamente'), 
        ('ESTERNA', 'Servizio Esterno'), 
        ('NONE', 'Non Usata')
    ]
    PATCH_CHOICES = [
        ('AUTOMATICO', 'Automatico'), 
        ('MANUALE', 'Manuale Periodico'), 
        ('ASSENTE', 'Assente/No Policy')
    ]
    
    azienda = models.OneToOneField(Azienda, on_delete=models.CASCADE, related_name='configurazione_rete', verbose_name=_("Azienda"))
    tipo_architettura = models.CharField(max_length=50, choices=ARCHITETTURA_CHOICES, default='HIERARCHICAL', verbose_name=_("Tipo di Architettura di Rete"))
    segmentazione_rete = models.TextField(verbose_name=_("Descrizione Segmentazione/VLAN"), blank=True, null=True)
    firewall_utilizzato = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Modello/Nome Firewall"))
    sistema_ids_ips = models.BooleanField(default=False, verbose_name=_("Sistema IDS/IPS Attivo"))
    gestione_antivirus_centralizzata = models.BooleanField(default=False, verbose_name=_("Antivirus Centralizzato"))
    gestione_vpn = models.CharField(max_length=50, choices=VPN_CHOICES, default='NONE', verbose_name=_("Gestione Accesso Remoto (VPN)"))
    politica_patching = models.CharField(max_length=50, choices=PATCH_CHOICES, default='MANUALE', verbose_name=_("Politica di Patch Management"))
    
    class Meta:
        verbose_name = _("Configurazione di Rete")
        verbose_name_plural = _("Configurazioni di Rete")

    def __str__(self):
        return f"Configurazione Rete per {self.azienda.nome}"


class ComponenteRete(models.Model):
    """ Modello per rappresentare i singoli device/nodi aggiunti come "caselle". """
    TIPO_COMPONENT_CHOICES = [
        ('DEVICE', 'Dispositivo Utente'),
        ('SERVER', 'Server/Virtual Host'),
        ('FIREWALL', 'Firewall/Router'),
        ('PRINTER', 'Stampante/Scanner'),
        ('HUB', 'Switch/Hub'),
        ('OTHER', 'Altro Nodo')
    ]
    
    configurazione = models.ForeignKey(
        ConfigurazioneRete, 
        on_delete=models.CASCADE, 
        related_name='componenti', 
        verbose_name=_("Configurazione Rete Madre")
    )
    
    nome_componente = models.CharField(max_length=100, verbose_name=_("Nome/Identificativo"))
    tipo = models.CharField(max_length=50, choices=TIPO_COMPONENT_CHOICES, default='DEVICE', verbose_name=_("Tipo Componente"))
    descrizione_funzione = models.TextField(blank=True, verbose_name=_("Funzione e Posizione"))
    criticita = models.CharField(max_length=20, choices=[('BASSA', 'Bassa'), ('MEDIA', 'Media'), ('ALTA', 'Alta')], default='MEDIA', verbose_name=_("Criticità Sicurezza"))
    
    # === CAMPO IP ===
    indirizzo_ip = models.CharField(max_length=45, blank=True, null=True, verbose_name=_("Indirizzo IP/Subnet"))
    # ===============================

    class Meta:
        verbose_name = _("Componente di Rete")
        verbose_name_plural = _("Componenti di Rete")
        ordering = ['tipo', 'nome_componente']
        
    def __str__(self):
        return self.nome_componente
        
# ==============================================================================
# 11. ASSET E SOFTWARE
# ==============================================================================

class Asset(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    tipo_asset = models.CharField(max_length=50, choices=[('PC', 'PC/Laptop'), ('SERVER', 'Server'), ('MOBILE', 'Smartphone/Tablet'), ('ALTRO', 'Altro')])
    marca_modello = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, blank=True)
    utente_assegnatario = models.CharField(max_length=100, blank=True)
    reparto = models.CharField(max_length=100, blank=True)
    luogo_fisico = models.CharField(max_length=100, blank=True)
    tratta_dati_personali = models.BooleanField(default=True)
    categoria_dati = models.CharField(max_length=50, choices=[('COMUNI', 'Comuni'), ('PARTICOLARI', 'Particolari'), ('GIUDIZIARI', 'Giudiziari')], default='COMUNI')
    criticita = models.CharField(max_length=20, choices=[('BASSA', 'Bassa'), ('MEDIA', 'Media'), ('ALTA', 'Alta')], default='MEDIA')
    disco_crittografato = models.BooleanField(default=False)
    antivirus_installato = models.BooleanField(default=False)
    stato = models.CharField(max_length=20, choices=[('IN_USO', 'In Uso'), ('DISMESSO', 'Dismesso'), ('MANUTENZIONE', 'In Manutenzione')], default='IN_USO')
    codice_inventario = models.CharField(max_length=50, blank=True)
    
class Software(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    nome_software = models.CharField(max_length=100)
    scopo_utilizzo = models.CharField(max_length=200)
    tipologia = models.CharField(max_length=20, choices=[('LOCALE', 'Installato Locale'), ('CLOUD', 'SaaS/Cloud'), ('APP', 'App Mobile')])
    fornitore = models.CharField(max_length=100, blank=True)
    locazione_server = models.CharField(max_length=100, blank=True, help_text="Es. Italia, Irlanda, USA")
    amministratore = models.CharField(max_length=100, blank=True, help_text="Chi gestisce questo software")

# ==============================================================================
# 12. ORGANIGRAMMA
# ==============================================================================

class RuoloPrivacy(models.Model):
    # La chiave Azienda è una Foreign Key a Azienda (necessario per Admin/Formset)
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    
    # Corretto RUOLO_CHOICES con max_length sufficiente per RESPONSABILE_TRATTAMENTO
    RUOLO_CHOICES = (
        ('TITOLARE', 'Titolare del Trattamento'), 
        ('RESPONSABILE_TRATTAMENTO', 'Responsabile del Trattamento'), 
        ('DPO', 'DPO'), 
        ('REFERENTE', 'Referente Privacy'), 
        ('ADS', 'Amministratore Sistema'), 
        ('AUTORIZZATO', 'Autorizzato'), 
        ('ESTERNO', 'Resp. Esterno')
    )
    ruolo_tipo = models.CharField(max_length=30, choices=RUOLO_CHOICES, verbose_name=_("Tipo di Ruolo Privacy"))
    
    # Campo per list_display (risolve E108)
    nome_cognome = models.CharField(max_length=100)
    contatti = models.CharField(max_length=200, blank=True)
    atto_nomina = models.FileField(upload_to='nomine/', blank=True, null=True)

    class Meta:
        verbose_name = _("Ruolo Privacy")
        verbose_name_plural = _("Ruoli Privacy")
        
# ==============================================================================
# 13. TIA (TRANSFER IMPACT ASSESSMENT)
# ==============================================================================

class Paese(models.Model):
    nome = models.CharField(max_length=100)
    adeguatezza_ue = models.BooleanField(default=False)
    gruppo_tia = models.IntegerField(default=3, help_text="1=Sicuro, 2=Medio, 3=Rischio")
    def __str__(self): return self.nome

class ValutazioneTIA(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    fornitore = models.CharField(max_length=100)
    paese_destinazione = models.ForeignKey(Paese, on_delete=models.SET_NULL, null=True)
    descrizione_dati = models.TextField()
    data_valutazione = models.DateField(auto_now_add=True)
    compilato_da = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    esito_calcolato = models.CharField(max_length=20, default='ROSSO') 
    note = models.TextField(blank=True)

# ==============================================================================
# 14. VIDEOSORVEGLIANZA
# ==============================================================================

class Videosorveglianza(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    nome_impianto = models.CharField(max_length=100, default="Impianto Principale")
    scopo = models.CharField(max_length=200, default="Sicurezza Patrimonio")
    numero_telecamere = models.IntegerField(default=1)
    tempo_conservazione = models.CharField(max_length=50, choices=[('24H', '24 Ore'), ('48H', '48 Ore'), ('72H', '72 Ore'), ('7GG', '7 Giorni (Richiede accordo)')], default='24H')
    cartelli_esposti = models.BooleanField(default=False)
    accordo_sindacale = models.BooleanField(default=False)
    autorizzazione_itl = models.BooleanField(default=False)
    dvr_conforme = models.BooleanField(default=False) 
    stato_conformita = models.CharField(max_length=20, default='NON_CONFORME')
    azioni_richieste = models.TextField(blank=True)
    data_compilazione = models.DateField(auto_now_add=True)
    compilato_da = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    registrazione_attiva = models.BooleanField(default=True)


# ==============================================================================
# 17. MODULO 7: GESTIONE REFERENTE CSIRT (NIS2)
# ==============================================================================

class ReferenteCSIRT(models.Model):
    """Modello per memorizzare la nomina del Referente CSIRT e i relativi dati."""
    azienda = models.OneToOneField(Azienda, on_delete=models.CASCADE, related_name='referente_csirt', verbose_name=_("Azienda"))
    data_nomina = models.DateField(default=timezone.now, verbose_name=_("Data Nomina"))
    
    pc_nome = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Nome Punto di Contatto"), help_text="Chi effettua la designazione")
    pc_cognome = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Cognome Punto di Contatto"))
    pc_email = models.EmailField(blank=True, null=True, verbose_name=_("Email Punto di Contatto"))
    
    codice_ipa = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Codice IPA"), help_text="Solo per Pubbliche Amministrazioni")

    referente_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='csirt_principal', verbose_name=_("Utente Sistema (Opzionale)"))
    
    ref_nome = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Nome Referente"))
    ref_cognome = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Cognome Referente"))
    ref_cf = models.CharField(max_length=16, blank=True, null=True, verbose_name=_("Codice Fiscale Referente"))
    ref_email = models.EmailField(blank=True, null=True, verbose_name=_("Email Referente (Istituzionale)"))
    ref_telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Telefono Reperibilità (H24)"))
    ref_ruolo = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Ruolo Aziendale"), help_text="Es. CISO, IT Manager, Consulente Esterno")
    
    sos1_nome = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Nome Sostituto 1"))
    sos1_cognome = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Cognome Sostituto 1"))
    sos1_cf = models.CharField(max_length=16, blank=True, null=True, verbose_name=_("CF Sostituto 1"))
    sos1_email = models.EmailField(blank=True, null=True, verbose_name=_("Email Sostituto 1"))
    
    sos2_nome = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Nome Sostituto 2"))
    sos2_cognome = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Cognome Sostituto 2"))
    sos2_cf = models.CharField(max_length=16, blank=True, null=True, verbose_name=_("CF Sostituto 2"))
    sos2_email = models.EmailField(blank=True, null=True, verbose_name=_("Email Sostituto 2"))

    competenze_documentate = models.BooleanField(default=False, verbose_name=_("Competenza documentata"))
    motivo_esterno = models.TextField(blank=True, null=True, verbose_name=_("Motivazione Scelta Esterna"))

    def __str__(self):
        return f"Referente CSIRT per {self.azienda.nome}"
    
    class Meta:
        verbose_name = _("Referente CSIRT (NIS2)")
        verbose_name_plural = _("Gestione Referente CSIRT (NIS2)")

class NotificaIncidente(models.Model):
    # Tassonomia ACN (Esempio basato su ransomware, DDOS, ecc.)
    CATEGORIA_CHOICES = (
        ('RANSOMWARE', _('Ransomware')),
        ('DDOS', _('Attacco DDOS')),
        ('PHISHING', _('Phishing/Spear-Phishing')),
        ('ACCESS_VIOLATION', _('Violazione di Accesso / Compromissione Account')),
        ('MALWARE', _('Malware (Generico)')),
    )

    IMPATTO_CHOICES = (
        ('CRITICO', _('Critico (Interruzione Totale)')),
        ('ALTO', _('Alto (Servizi Essenziali Impattati)')),
        ('MEDIO', _('Medio (Impatto su Servizi Secondari)')),
        ('BASSO', _('Basso (Danno Minimo)')),
    )

    # Playbook: Riferimento ai documenti operativi (Appendice C ACN)
    PLAYBOOK_CHOICES = (
        ('RANSOMWARE_P', _('Playbook Ransomware')),
        ('DDOS_P', _('Playbook DDOS')),
        ('PHISHING_P', _('Playbook Phishing')),
        ('GENERIC_P', _('Playbook Generico')),
    )
    
    STATO_CHOICES = (
        ('APERTA', _('Aperta')),
        ('IN_RISPOSTA', _('In Risposta/Gestione')),
        ('NOTIFICATA', _('Notificata ACN')),
        ('CHIUSA', _('Chiusa')),
    )
    
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE, related_name='notifiche_incidenti')
    referente_csirt = models.ForeignKey(ReferenteCSIRT, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Referente che ha notificato"))
    
    titolo_incidente = models.CharField(max_length=255, verbose_name=_("Titolo Incidente NIS2"))
    data_incidente = models.DateTimeField(verbose_name=_("Data e Ora Incidente"))
    data_notifica = models.DateTimeField(null=True, blank=True, verbose_name=_("Data Notifica ACN"))
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='APERTA', verbose_name=_("Stato Notifica"))
    descrizione_danno = models.TextField(verbose_name=_("Descrizione Danno/Impatto"))
    
    # === NUOVI CAMPI DI CARATTERIZZAZIONE ACN/NIST (Punto 3) ===
    categoria_incidente = models.CharField(
        max_length=50, 
        choices=CATEGORIA_CHOICES, 
        default='MALWARE',
        verbose_name=_("Categoria Incidente (Tassonomia ACN)")
    )
    impatto_stimato = models.CharField(
        max_length=20,
        choices=IMPATTO_CHOICES,
        default='ALTO',
        verbose_name=_("Impatto stimato (Operativo/Finanziario)")
    )
    # La Severità (o Criticità) è spesso una combinazione di categoria e impatto, ma la registriamo
    severita_incidente = models.CharField(
        max_length=20,
        choices=IMPATTO_CHOICES, # Riutilizziamo la scala per semplicità
        default='ALTO',
        verbose_name=_("Severità/Criticità (Decisa dall'IR Team)")
    )
    
    playbook_associato = models.CharField(
        max_length=50, 
        choices=PLAYBOOK_CHOICES, 
        blank=True, 
        null=True,
        verbose_name=_("Playbook di Risposta")
    )
    # =============================================================
    
    # Campi esistenti:
    valutazione_rischio = models.TextField(blank=True, null=True, verbose_name=_("Valutazione Rischio e Danno"))
    azioni_correttive = models.TextField(blank=True, null=True, verbose_name=_("Azioni Correttive Adottate"))

    def __str__(self):
        return f"Notifica {self.titolo_incidente} - {self.azienda.nome}"
    
    class Meta:
        verbose_name = _("Notifica Incidente NIS2")
        verbose_name_plural = _("Registro Notifiche NIS2")

# ==============================================================================
# 18. ALLEGATI PER NOTIFICHE INCIDENTI
# ==============================================================================

class AllegatoNotifica(models.Model):
    """
    Modello per gli allegati relativi a una Notifica Incidente specifica (es. log, screenshot).
    """
    notifica = models.ForeignKey(
        NotificaIncidente, 
        on_delete=models.CASCADE, 
        related_name='allegati', 
        verbose_name=_("Notifica Incidente")
    )
    file = models.FileField(upload_to='csirt_allegati/', verbose_name=_("File Allegato"))
    descrizione = models.CharField(max_length=255, blank=True, verbose_name=_("Descrizione"))
    data_caricamento = models.DateTimeField(auto_now_add=True)
    caricato_da = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = _("Allegato Notifica")
        verbose_name_plural = _("Allegati Notifiche")