import requests
from prometheus_api_client import PrometheusConnect
from django.utils import timezone
from .models import AssetMonitorato, LogMonitoraggio

class PrometheusManager:
    def __init__(self, url="http://localhost:9090"):
        self.prom = PrometheusConnect(url=url, disable_ssl=True)

    def check_assets_availability(self):
        assets = AssetMonitorato.objects.filter(is_attivo=True)
        results = []
        for asset in assets:
            query = f'up{{instance="{asset.indirizzo_ip}:{asset.porta_monitoraggio}"}}'
            try:
                data = self.prom.custom_query(query=query)
                is_up = (data[0]['value'][1] == '1') if data else False
                LogMonitoraggio.objects.create(asset=asset, stato_up=is_up)
                results.append({'asset': asset.nome, 'status': 'ONLINE' if is_up else 'OFFLINE'})
            except Exception:
                results.append({'asset': asset.nome, 'status': 'ERROR'})
        return results

    def get_cpu_usage(self, asset):
        query = f'100 - (avg by (instance) (irate(node_cpu_seconds_total{{instance="{asset.indirizzo_ip}:{asset.porta_monitoraggio}",mode="idle"}}[5m])) * 100)'
        try:
            data = self.prom.custom_query(query=query)
            return round(float(data[0]['value'][1]), 2) if data else 0
        except Exception:
            return 0

class DeashedManager:
    """
    Gestore per le API di DeHashed.com.
    Monitora l'esposizione delle credenziali (Cyber Hygiene NIS2 Art. 21.2).
    """
    def __init__(self, api_key="TUA_API_KEY", username="TUO_USERNAME_DEHASHED"):
        self.api_key = api_key
        self.username = username
        self.base_url = "https://deashed.com/api/v1/search"

    def check_domain_exposure(self, domain):
        """
        Interroga DeHashed per trovare leak legati al dominio aziendale.
        """
        # In fase di test locale, se non hai l'API Key, puoi decommentare la riga sotto
        # return 5  # Simula 5 leak trovati
        
        params = {'query': f'domain:{domain}', 'size': 1}
        try:
            # La chiamata richiede autenticazione Basic (username:api_key)
            response = requests.get(
                self.base_url, 
                params=params, 
                auth=(self.username, self.api_key),
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('total', 0)
        except Exception:
            return 0
        return 0