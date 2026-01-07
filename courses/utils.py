import requests
import urllib3
from .models import ImpostazioniSito

# Disabilitiamo gli avvisi SSL per sicurezza durante i test di connessione
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_dns_report(dominio):
    """
    Interroga lo strumento propagation di ViewDNS e restituisce la lista dei server. 🌐
    """
    # 1. Recupero della configurazione
    try:
        config = ImpostazioniSito.objects.get(pk=1)
        api_key = config.viewdns_api_key
    except ImpostazioniSito.DoesNotExist:
        return {"error": "Configurazione ImpostazioniSito non trovata."}

    if not api_key:
        return {"error": "API Key di ViewDNS non configurata."}

    # 2. Definizione dell'URL per la propagazione (quello che ha funzionato!) 🚀
    base_url = "https://api.viewdns.info/propagation/"
    
    params = {
        'domain': dominio,
        'apikey': api_key,
        'output': 'json'
    }

    # 3. Chiamata all'API
    try:
        response = requests.get(base_url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Estraiamo la lista 'server' che abbiamo visto nel terminale
        # Se non esiste, restituiamo una lista vuota per evitare errori nel template
        return data.get('response', {}).get('server', [])
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Errore di connessione: {e}"}