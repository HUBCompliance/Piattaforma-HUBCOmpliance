from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .utils import PrometheusManager, DeashedManager  # Assicurati che DeashedManager sia in utils.py
from .models import AssetMonitorato
from compliance.views import get_azienda_current  # Helper per recuperare l'azienda dell'utente

@login_required
def dashboard_monitoraggio(request):
    """
    Vista 'Semaforo Tecnico' integrata con Threat Intelligence (DeHashed).
    Fornisce una visione olistica della postura di sicurezza conforme alla NIS2.
    """
    # 1. Recupero dell'azienda associata all'utente
    azienda = get_azienda_current(request)
    
    # --- PARTE A: MONITORAGGIO INFRASTRUTTURA (PROMETHEUS) ---
    # Requisito NIS2: Gestione della disponibilità e monitoraggio incidenti (Art. 21)
    pm = PrometheusManager()
    
    # Esegue il controllo live (es. ping/http check via Prometheus)
    status_live = pm.check_assets_availability()
    
    # Recupera gli asset attivi dell'azienda
    assets = AssetMonitorato.objects.filter(azienda=azienda, is_attivo=True)
    
    tabella_semaforo = []
    for asset in assets:
        # Recupero carico CPU attuale per prevenire saturazioni
        cpu_load = pm.get_cpu_usage(asset)
        
        # Individua lo stato online/offline dai dati live
        status_info = next((item for item in status_live if item['asset'] == asset.nome), None)
        is_online = status_info['status'] == 'ONLINE' if status_info else False
        
        # Logica del colore per il semaforo tecnico (Monitoraggio proattivo)
        if not is_online:
            color_class = "bg-danger"   # Rosso: Asset non raggiungibile
        elif cpu_load and cpu_load > asset.soglia_allarme_cpu:
            color_class = "bg-warning"  # Giallo: Superamento soglie critiche
        else:
            color_class = "bg-success"  # Verde: Operatività nominale
            
        tabella_semaforo.append({
            'asset': asset,
            'is_online': is_online,
            'cpu_usage': cpu_load,
            'color': color_class
        })

    # --- PARTE B: THREAT INTELLIGENCE (DEHASHED API) ---
    # Requisito NIS2: Protezione contro l'accesso non autorizzato e Cyber Hygiene (Art. 21.2)
    dm = DeashedManager()
    
    # Definiamo il dominio da monitorare (se non presente nel modello azienda, usiamo un fallback)
    dominio_aziendale = getattr(azienda, 'dominio_web', 'azienda.com')
    
    # Interroga le API DeHashed per cercare leak di email/password legate al dominio
    leak_count = dm.check_domain_exposure(dominio_aziendale)
    
    # Valutazione del rischio di esposizione esterna
    if leak_count == 0:
        rischio_esposizione = "BASSO"
        deashed_color = "text-success"
    elif leak_count < 20:
        rischio_esposizione = "MEDIO"
        deashed_color = "text-warning"
    else:
        rischio_esposizione = "ALTO"
        deashed_color = "text-danger"

    # 2. Preparazione del contesto per il template
    context = {
        'tabella_semaforo': tabella_semaforo,
        'leak_count': leak_count,
        'rischio_esposizione': rischio_esposizione,
        'deashed_color': deashed_color,
        'titolo_pagina': "Semaforo Tecnico & Threat Intelligence (NIS2)",
        'azienda': azienda,
        'dominio_monitorato': dominio_aziendale
    }
    
    return render(request, 'monitoring/dashboard_tecnica.html', context)