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
    class Meta:
        verbose_name = "Categoria Audit"
        verbose_name_plural = "Categorie Audit"

class SoggettoInteressato(models.Model):
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome
    class Meta:
        verbose_name = "Soggetto Interessato"
        verbose_name_plural = "Soggetti Interessati"

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
    class Meta:
        verbose_name = "Trattamento"
        verbose_name_plural = "Trattamenti"

    def __str__(self): return self.nome_trattamento

class DomandaChecklist(models.Model):
    testo = models.TextField()
    punteggio_rischio = models.IntegerField(default=1)
    ordine = models.IntegerField(default=0)
    def __str__(self): return self.testo
    class Meta:
        verbose_name = "Domanda"
        verbose_name_plural = "Domande"
    

class RispostaChecklist(models.Model):
    trattamento = models.ForeignKey(Trattamento, on_delete=models.CASCADE, related_name='risposte_checklist')
    domanda = models.ForeignKey(DomandaChecklist, on_delete=models.CASCADE)
    risposta = models.BooleanField(default=False) # True = Sì (Rischio presente)

# ==============================================================================
# 2. GESTIONE DOCUMENTALE
# ==============================================================================

class CategoriaDocumento(models.Model):
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome
    class Meta:
        verbose_name = "Categoria Documento"
        verbose_name_plural = "Categorie Documenti"

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
    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documenti"

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
    class Meta:
        verbose_name = "Incidente"
        verbose_name_plural = "Incidenti"

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
    class Meta:
        verbose_name = "Richiesta Interessato"
        verbose_name_plural = "Richiesta Interessati"

# ==============================================================================
# 5. AUDIT GENERALE (Con Metodi di Calcolo)
# ==============================================================================

class AuditCategoria(models.Model):
    nome = models.CharField(max_length=100)
    ordine = models.IntegerField(default=0)
    def __str__(self): return self.nome
    class Meta:
        verbose_name = "Categoria Audit"
        verbose_name_plural = "Categorie Audit"

class AuditDomanda(models.Model):
    categoria = models.ForeignKey(AuditCategoria, on_delete=models.CASCADE, related_name='domande')
    testo = models.TextField()
    ordine = models.IntegerField(default=0)
    def __str__(self): return self.testo
    class Meta:
        verbose_name = "Domanda Audit"
        verbose_name_plural = "Domande Audit"

class AuditSession(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    data_creazione = models.DateTimeField(auto_now_add=True)
    creato_da = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    completato = models.BooleanField(default=False)
    note = models.TextField(blank=True)
    archiviata = models.BooleanField(default=False)  # Nuovo campo
    @property
    def is_frozen(self):
        return self.archiviata
    @property
    def percentuale_completamento(self):
        """Calcola la percentuale basata su risposte Boolean (True/False)."""
        risposte = self.risposte.all()
        totale = risposte.count()
        if totale == 0:
            return 0.0
        positivi = risposte.filter(risposta=True).count()
        return round((positivi / totale) * 100, 1)

    @property
    def colore_rating(self):
        """Restituisce il colore per la dashboard."""
        p = self.percentuale_completamento
        if p >= 80: return "success"
        elif p >= 50: return "warning"
        else: return "danger"

    class Meta:
        verbose_name = "Sessione Audit"
        verbose_name_plural = "Sessioni Audit"

class AuditRisposta(models.Model):
    sessione = models.ForeignKey(AuditSession, on_delete=models.CASCADE, related_name='risposte')
    domanda = models.ForeignKey(AuditDomanda, on_delete=models.CASCADE)
    risposta = models.BooleanField(default=False) # Sì/No
    note = models.TextField(blank=True)
    class Meta: 
        unique_together = ('sessione', 'domanda')
        verbose_name = "Risposta Audit"
        verbose_name_plural = "Risposte Audit"

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
    class Meta:
        verbose_name = "Compito"
        verbose_name_plural = "Compiti"

# ==============================================================================
# 7. CONFIGURAZIONE DI RETE
# ==============================================================================

class ConfigurazioneRete(models.Model):
    ARCHITETTURA_CHOICES = [('STAR', 'Star'), ('MESH', 'Mesh'), ('HIERARCHICAL', 'Gerarchica'), ('FLAT', 'Piatta')]
    VPN_CHOICES = [('AZIENDA', 'Gestita Internamente'), ('ESTERNA', 'Servizio Esterno'), ('NONE', 'Non Usata')]
    PATCH_CHOICES = [('AUTOMATICO', 'Automatico'), ('MANUALE', 'Manuale Periodico'), ('ASSENTE', 'Assente/No Policy')]

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

    def __str__(self): return f"Configurazione Rete per {self.azienda.nome}"

class ComponenteRete(models.Model):
    TIPO_COMPONENT_CHOICES = [('DEVICE', 'Dispositivo Utente'), ('SERVER', 'Server/Virtual Host'), ('FIREWALL', 'Firewall/Router'), ('PRINTER', 'Stampante/Scanner'), ('HUB', 'Switch/Hub'), ('OTHER', 'Altro Nodo')]
    configurazione = models.ForeignKey(ConfigurazioneRete, on_delete=models.CASCADE, related_name='componenti', verbose_name=_("Configurazione Rete Madre"))
    nome_componente = models.CharField(max_length=100, verbose_name=_("Nome/Identificativo"))
    tipo = models.CharField(max_length=50, choices=TIPO_COMPONENT_CHOICES, default='DEVICE', verbose_name=_("Tipo Componente"))
    descrizione_funzione = models.TextField(blank=True, verbose_name=_("Funzione e Posizione"))
    criticita = models.CharField(max_length=20, choices=[('BASSA', 'Bassa'), ('MEDIA', 'Media'), ('ALTA', 'Alta')], default='MEDIA', verbose_name=_("Criticità Sicurezza"))
    indirizzo_ip = models.CharField(max_length=45, blank=True, null=True, verbose_name=_("Indirizzo IP/Subnet"))

    class Meta:
        verbose_name = _("Componente di Rete")
        verbose_name_plural = _("Componenti di Rete")
        ordering = ['tipo', 'nome_componente']

    def __str__(self): return self.nome_componente

# ==============================================================================
# 8. ASSET E SOFTWARE
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
    class Meta:
        verbose_name = "Asset"
        verbose_name_plural = "Asset"

class Software(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    nome_software = models.CharField(max_length=100)
    scopo_utilizzo = models.CharField(max_length=200)
    tipologia = models.CharField(max_length=20, choices=[('LOCALE', 'Installato Locale'), ('CLOUD', 'SaaS/Cloud'), ('APP', 'App Mobile')])
    fornitore = models.CharField(max_length=100, blank=True)
    locazione_server = models.CharField(max_length=100, blank=True, help_text="Es. Italia, Irlanda, USA")
    amministratore = models.CharField(max_length=100, blank=True)
    class Meta:
        verbose_name = "Software"
        verbose_name_plural = "Software"

# ==============================================================================
# 9. ORGANIGRAMMA
# ==============================================================================

class RuoloPrivacy(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    RUOLO_CHOICES = (('TITOLARE', 'Titolare del Trattamento'), ('RESPONSABILE_TRATTAMENTO', 'Responsabile del Trattamento'), ('DPO', 'DPO'), ('REFERENTE', 'Referente Privacy'), ('ADS', 'Amministratore Sistema'), ('AUTORIZZATO', 'Autorizzato'), ('ESTERNO', 'Resp. Esterno'))
    ruolo_tipo = models.CharField(max_length=30, choices=RUOLO_CHOICES, verbose_name=_("Tipo di Ruolo Privacy"))
    nome_cognome = models.CharField(max_length=100)
    contatti = models.CharField(max_length=200, blank=True)
    atto_nomina = models.FileField(upload_to='nomine/', blank=True, null=True)

    class Meta:
        verbose_name = _("Ruolo Privacy")
        verbose_name_plural = _("Ruoli Privacy")

# ==============================================================================
# 10. TIA (TRANSFER IMPACT ASSESSMENT)
# ==============================================================================

class Paese(models.Model):
    nome = models.CharField(max_length=100)
    adeguatezza_ue = models.BooleanField(default=False)
    gruppo_tia = models.IntegerField(default=3, help_text="1=Sicuro, 2=Medio, 3=Rischio")
    def __str__(self): return self.nome
    class Meta:
        verbose_name = "Paese"
        verbose_name_plural = "Paesi"

class ValutazioneTIA(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    fornitore = models.CharField(max_length=100)
    paese_destinazione = models.ForeignKey(Paese, on_delete=models.SET_NULL, null=True)
    descrizione_dati = models.TextField()
    data_valutazione = models.DateField(auto_now_add=True)
    compilato_da = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    esito_calcolato = models.CharField(max_length=20, default='ROSSO')
    note = models.TextField(blank=True)
    class Meta:
        verbose_name = "Valutazione TIA"
        verbose_name_plural = "Valutazioni TIA"

# ==============================================================================
# 11. VIDEOSORVEGLIANZA
# ==============================================================================

class Videosorveglianza(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE)
    nome_impianto = models.CharField(max_length=100, default="Impianto Principale")
    scopo = models.CharField(max_length=200, default="Sicurezza Patrimonio")
    numero_telecamere = models.IntegerField(default=1)
    tempo_conservazione = models.CharField(max_length=50, choices=[('24H', '24 Ore'), ('48H', '48 Ore'), ('72H', '72 Ore'), ('7GG', '7 Giorni')], default='24H')
    cartelli_esposti = models.BooleanField(default=False)
    accordo_sindacale = models.BooleanField(default=False)
    autorizzazione_itl = models.BooleanField(default=False)
    dvr_conforme = models.BooleanField(default=False)
    stato_conformita = models.CharField(max_length=20, default='NON_CONFORME')
    azioni_richieste = models.TextField(blank=True)
    data_compilazione = models.DateField(auto_now_add=True)
    compilato_da = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    registrazione_attiva = models.BooleanField(default=True)
    class Meta:
        verbose_name = "Impianto Videosorveglianza"
        verbose_name_plural = "Impianti Videosorveglianza"


# ==============================================================================
# 12. GESTIONE REFERENTE CSIRT (NIS2)
# ==============================================================================

class ReferenteCSIRT(models.Model):
    azienda = models.OneToOneField(Azienda, on_delete=models.CASCADE, related_name='referente_csirt', verbose_name=_("Azienda"))
    data_nomina = models.DateField(default=timezone.now, verbose_name=_("Data Nomina"))
    pc_nome = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Nome Punto di Contatto"))
    pc_cognome = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Cognome Punto di Contatto"))
    pc_email = models.EmailField(blank=True, null=True, verbose_name=_("Email Punto di Contatto"))
    codice_ipa = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Codice IPA"))
    referente_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='csirt_principal')
    ref_nome = models.CharField(max_length=100, blank=True, null=True)
    ref_cognome = models.CharField(max_length=100, blank=True, null=True)
    ref_cf = models.CharField(max_length=16, blank=True, null=True)
    ref_email = models.EmailField(blank=True, null=True)
    ref_telefono = models.CharField(max_length=20, blank=True, null=True)
    ref_ruolo = models.CharField(max_length=100, blank=True, null=True)
    sos1_nome = models.CharField(max_length=100, blank=True, null=True)
    sos1_cognome = models.CharField(max_length=100, blank=True, null=True)
    sos1_cf = models.CharField(max_length=16, blank=True, null=True)
    sos1_email = models.EmailField(blank=True, null=True)
    sos2_nome = models.CharField(max_length=100, blank=True, null=True)
    sos2_cognome = models.CharField(max_length=100, blank=True, null=True)
    sos2_cf = models.CharField(max_length=16, blank=True, null=True)
    sos2_email = models.EmailField(blank=True, null=True)
    competenze_documentate = models.BooleanField(default=False)
    motivo_esterno = models.TextField(blank=True, null=True)

    def __str__(self): return f"Referente CSIRT per {self.azienda.nome}"
    class Meta:
        verbose_name = _("Referente CSIRT (NIS2)")
        verbose_name_plural = _("Gestione Referente CSIRT (NIS2)")

class NotificaIncidente(models.Model):
    CATEGORIA_CHOICES = (('RANSOMWARE', _('Ransomware')), ('DDOS', _('Attacco DDOS')), ('PHISHING', _('Phishing')), ('ACCESS_VIOLATION', _('Violazione Account')), ('MALWARE', _('Malware')))
    IMPATTO_CHOICES = (('CRITICO', _('Critico')), ('ALTO', _('Alto')), ('MEDIO', _('Medio')), ('BASSO', _('Basso')))
    PLAYBOOK_CHOICES = (('RANSOMWARE_P', _('Playbook Ransomware')), ('DDOS_P', _('Playbook DDOS')), ('PHISHING_P', _('Playbook Phishing')), ('GENERIC_P', _('Playbook Generico')))
    STATO_CHOICES = (('APERTA', _('Aperta')), ('IN_RISPOSTA', _('In Risposta')), ('NOTIFICATA', _('Notificata ACN')), ('CHIUSA', _('Chiusa')))

    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE, related_name='notifiche_incidenti')
    referente_csirt = models.ForeignKey(ReferenteCSIRT, on_delete=models.SET_NULL, null=True, blank=True)
    titolo_incidente = models.CharField(max_length=255)
    data_incidente = models.DateTimeField()
    data_notifica = models.DateTimeField(null=True, blank=True)
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='APERTA')
    descrizione_danno = models.TextField()
    categoria_incidente = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, default='MALWARE')
    impatto_stimato = models.CharField(max_length=20, choices=IMPATTO_CHOICES, default='ALTO')
    severita_incidente = models.CharField(max_length=20, choices=IMPATTO_CHOICES, default='ALTO')
    playbook_associato = models.CharField(max_length=50, choices=PLAYBOOK_CHOICES, blank=True, null=True)
    valutazione_rischio = models.TextField(blank=True, null=True)
    azioni_correttive = models.TextField(blank=True, null=True)

    def __str__(self): return f"Notifica {self.titolo_incidente} - {self.azienda.nome}"
    class Meta:
        verbose_name = _("Notifica Incidente NIS2")
        verbose_name_plural = _("Registro Notifiche NIS2")

class AllegatoNotifica(models.Model):
    notifica = models.ForeignKey(NotificaIncidente, on_delete=models.CASCADE, related_name='allegati')
    file = models.FileField(upload_to='csirt_allegati/')
    descrizione = models.CharField(max_length=255, blank=True)
    data_caricamento = models.DateTimeField(auto_now_add=True)
    caricato_da = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        verbose_name = "Allegato Notifica"
        verbose_name_plural = "Allegati Notifiche"

# ==============================================================================
# 13. SECURITY CHECKLIST (Con Metodi di Calcolo Bonificati)
# ==============================================================================

class SecurityControl(models.Model):
    area = models.CharField(max_length=255, verbose_name=_("Area di Controllo"))
    control_id = models.CharField(max_length=50, verbose_name=_("ID Controllo"))
    descrizione = models.TextField(verbose_name=_("Descrizione Controllo"))
    supporto_verifica = models.TextField(blank=True, null=True)
    riferimento_iso = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = _("Controllo Security")
        verbose_name_plural = _("Controlli Security")
        ordering = ['control_id']
    def __str__(self): return f"{self.control_id} - {self.area}"

class SecurityAudit(models.Model):
    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE, related_name='security_audits')
    data_creazione = models.DateTimeField(auto_now_add=True)
    completato = models.BooleanField(default=False)
    creato_da = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    # === METODO BONIFICATO PER L'ERRORE ATTRIBUTEERROR ===
    def get_punteggio_area(self, area_nome):
        """Calcola la percentuale di conformità per una specifica area (es. Network, Asset)."""
        risposte = self.risposte.filter(controllo__area=area_nome)
        totale_validi = risposte.exclude(esito='NA').count()
        # Filtro fondamentale con l'accento 'SÌ' per il calcolo corretto
        positivi = risposte.filter(esito='SÌ').count() 
        if totale_validi == 0:
            return 0.0
        return round((positivi / totale_validi) * 100, 1)

    @property
    def punteggio_totale(self):
        """Calcola la percentuale globale basata su stringhe 'SÌ'."""
        risposte = self.risposte.all()
        totale_validi = risposte.exclude(esito='NA').count()
        positivi = risposte.filter(esito='SÌ').count() 
        if totale_validi == 0: return 0.0
        return round((positivi / totale_validi) * 100, 1)

    @property
    def colore_rating(self):
        """Restituisce la classe colore bootstrap per i widget."""
        p = self.punteggio_totale
        if p >= 80: return "success"
        elif p >= 50: return "warning"
        else: return "danger"

    class Meta:
        verbose_name = _("Audit Security")
        verbose_name_plural = _("Audit Security")
    def __str__(self): return f"Security Audit - {self.azienda.nome} ({self.data_creazione.strftime('%d/%m/%Y')})"

class SecurityResponse(models.Model):
    ESITO_CHOICES = [('SÌ', _('Sì')), ('NO', _('No')), ('IN_CORSO', _('In Corso')), ('NA', _('Non Applicabile'))]
    audit = models.ForeignKey(SecurityAudit, on_delete=models.CASCADE, related_name='risposte')
    controllo = models.ForeignKey(SecurityControl, on_delete=models.CASCADE)
    esito = models.CharField(max_length=10, choices=ESITO_CHOICES, default='NO')
    note = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('audit', 'controllo')
        verbose_name = "Risposta Security"
        verbose_name_plural = "Risposte Security"