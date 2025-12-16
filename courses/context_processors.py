from user_auth.models import Azienda # Assicurati che Azienda sia importata
from courses.models import ImpostazioniSito
from django.db.models import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.conf import settings 
from django.db.utils import ConnectionDoesNotExist, OperationalError

def site_settings(request):
    """
    Rende le impostazioni del sito (ImpostazioniSito) e il contesto dell'azienda corrente
    disponibili globalmente in tutti i template.
    
    Questa funzione include il fix critico per l'utente Consulente e la neutralizzazione 
    del contesto sulla pagina di login.
    """
    
    # 1. Caricamento Impostazioni Globali (SAFE)
    try:
        config_obj = ImpostazioniSito.objects.get(pk=1)
    except (ObjectDoesNotExist, OperationalError, ConnectionDoesNotExist):
        config_obj = None
        
    context = {'config': config_obj, 'azienda_corrente': None}
    
    # === GUARDRAIL 1: NEUTRALIZZAZIONE DEL CONTESTO NON AUTENTICATO (FIX LOGIN LOOP) ===
    # Controlla se request.user è autenticato prima di accedere al database.
    if not request.user.is_authenticated:
        # Quando non sei loggato, l'unica cosa che restituiamo è il contesto neutro (config)
        return context

    # === GUARDRAIL 2 E LOGICA PER UTENTE AUTENTICATO (FIX CONSULENTE ROUTING) ===
    
    user = request.user
    azienda_corrente = None
    context['config'] = config_obj # Manteniamo la config globale
    
    try:
        # REFERENTE: L'azienda è fissa
        if user.ruolo == 'REFERENTE' and hasattr(user, 'azienda'):
            try:
                azienda_corrente = user.azienda
            except Azienda.DoesNotExist:
                 azienda_corrente = None
        
        # CONSULENTE: L'azienda dipende dall'ID in sessione, impostato dalla vista Dashboard
        elif user.ruolo == 'CONSULENTE':
            azienda_id = request.session.get('consulente_azienda_id')
            if azienda_id:
                try:
                    # CORREZIONE CRITICA: Usa la relazione M2M diretta manager_users
                    # che è robusta per la verifica dei permessi
                    azienda_corrente = Azienda.objects.get(pk=azienda_id, manager_users=user)
                except Azienda.DoesNotExist:
                    # Se l'accesso fallisce, puliamo la sessione per prevenire il loop
                    if 'consulente_azienda_id' in request.session:
                        del request.session['consulente_azienda_id']
                    azienda_corrente = None
        
        context['azienda_corrente'] = azienda_corrente

    except Exception:
        # Cattura qualsiasi altro errore di DB/Relazione residuo
        context['azienda_corrente'] = None

    return context