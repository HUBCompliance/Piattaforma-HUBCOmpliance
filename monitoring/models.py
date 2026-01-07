from django.db import migrations, models
from compliance.models import Azienda  # Colleghiamo il monitoraggio all'azienda

class AssetMonitorato(models.Model):
    """
    Rappresenta un server o un servizio critico da monitorare (NIS2 Asset Management).
    """
    TIPO_ASSET = [
        ('SERVER', 'Server Fisico/VM'),
        ('DB', 'Database'),
        ('WEB', 'Sito Web / API'),
        ('NETWORK', 'Apparato di Rete (Firewall/Switch)'),
    ]

    azienda = models.ForeignKey(Azienda, on_delete=models.CASCADE, related_name='assets_monitorati')
    nome = models.CharField(max_length=100, help_text="Es: Server Produzione 01")
    tipologia = models.CharField(max_length=20, choices=TIPO_ASSET, default='SERVER')
    
    # Dati Tecnici per Prometheus/Zabbix
    indirizzo_ip = models.GenericIPAddressField(help_text="Indirizzo IP dell'asset")
    porta_monitoraggio = models.PositiveIntegerField(default=9100, help_text="Porta dell'exporter (es. 9100 per Node Exporter)")
    
    # Stato e Alerting
    is_attivo = models.BooleanField(default=True, help_text="Indica se il monitoraggio è attivo")
    soglia_allarme_cpu = models.PositiveIntegerField(default=90, help_text="Percentuale CPU per far scattare l'allerta")
    note_tecniche = models.TextField(blank=True, null=True)

    data_inserimento = models.DateTimeField(auto_now_add=True)
    ultima_modifica = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Asset Monitorato"
        verbose_name_plural = "Assets Monitorati"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.indirizzo_ip}) - {self.azienda.nome}"

class LogMonitoraggio(models.Model):
    """
    Storico degli incidenti tecnici rilevati (Utile per reportistica NIS2).
    """
    asset = models.ForeignKey(AssetMonitorato, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    stato_up = models.BooleanField(default=True)
    messaggio_errore = models.TextField(blank=True, null=True)
    durata_down = models.DurationField(null=True, blank=True)

    def __str__(self):
        status = "UP" if self.stato_up else "DOWN"
        return f"{self.asset.nome} - {status} al {self.timestamp}"