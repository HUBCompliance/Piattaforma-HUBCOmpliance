import os
from google import genai
from google.genai.errors import APIError

# Importiamo il modello ImpostazioniSito
# Deve importare il modello dall'app courses
try:
    from courses.models import ImpostazioniSito
except ImportError:
    # Fallback se l'import fallisce, ImpostazioniSito sarà None.
    print("ATTENZIONE: Impossibile importare ImpostazioniSito in ai_client.py. Assicurati che 'courses' sia in INSTALLED_APPS.")
    ImpostazioniSito = None
except Exception as e:
    # Gestione generica in caso di errore non previsto durante l'import (es. errore di migrazione)
    print(f"Errore critico durante l'importazione di ImpostazioniSito: {e}")
    ImpostazioniSito = None


def get_gemini_api_key():
    """Recupera la chiave API Gemini dal modello ImpostazioniSito nel database."""
    if ImpostazioniSito is None:
        return None 
    try:
        # Recupera l'unica istanza con PK=1 (Assumendo che ImpostazioniSito sia un Singleton)
        settings = ImpostazioniSito.objects.get(pk=1)
        # NOTA: Usiamo .strip() per rimuovere spazi bianchi o newline che potrebbero causare errori API
        return settings.gemini_api_key.strip() if settings.gemini_api_key else None
    except ImpostazioniSito.DoesNotExist:
        return None
    except Exception as e:
        # Questo cattura errori come Model not ready o problemi di connessione al DB
        return None


def generate_gemini_response(prompt: str) -> str:
    """
    Invia un prompt al modello Gemini, leggendo la chiave API dal database.
    """
    
    # 1. Recupera la chiave API dal database
    api_key = get_gemini_api_key()
    
    if not api_key:
        # Se la chiave non è disponibile, restituisce un messaggio d'errore gestibile
        return "Errore Configurazione: La chiave API Gemini non è stata trovata nel database ImpostazioniSito. Inseriscila nell'area Admin."

    try:
        # 2. Inizializzazione del Client con la chiave del DB
        client = genai.Client(api_key=api_key)
        
        # 3. Impostazione del modello e generazione
        model = 'gemini-2.5-flash'
        
        response = client.models.generate_content(
            model=model,
            contents=[prompt]
        )
        
        # 4. Restituzione del testo generato
        if response.candidates and response.candidates[0].content.parts:
            return response.text.strip()
        else:
            return "Il modello AI non ha prodotto una risposta valida."
            
    except APIError as e:
        # Gestione degli errori specifici dell'API (es. chiave non valida, quota esaurita)
        return f"Errore API Gemini: {e}. Controlla la tua chiave nel pannello di amministrazione."
    except Exception as e:
        # Gestione di altri errori
        return f"Errore Generale durante la chiamata AI: {e}"