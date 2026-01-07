from django import template
from compliance.models import RuoloPrivacy  # Assicurati che il nome del modello sia corretto

# Registra la libreria di tag/filtri
register = template.Library()

# --- FILTRI ESISTENTI ---

@register.filter
def get_item(dictionary, key):
    """Accede ai campi di un BoundField o dizionario."""
    try:
        return dictionary[key]
    except (TypeError, IndexError, KeyError):
        try:
            return getattr(dictionary, key)
        except AttributeError:
            return dictionary.get(key)
        except Exception:
            return None

@register.filter
def get_ruoli_by_type(azienda, ruolo_tipo):
    """Ritorna il primo RuoloPrivacy associato all'azienda per un dato ruolo_tipo."""
    try:
        return azienda.ruoloprivacy_set.filter(ruolo_tipo=ruolo_tipo).first()
    except AttributeError:
        return None

# --- NUOVO TAG PER LA PARTE VISIVA A BLOCCHI ---

@register.inclusion_tag('compliance/components/organigramma_tree.html')
def render_organigramma_visual(azienda):
    """
    Recupera tutti i ruoli salvati per l'azienda e li passa 
    al mini-template che disegna i blocchi grafici.
    """
    try:
        # Recuperiamo tutti i ruoli ordinati per tipo
        ruoli = RuoloPrivacy.objects.filter(azienda=azienda).order_by('ruolo_tipo')
    except Exception:
        ruoli = []
        
    return {
        'azienda': azienda,
        'ruoli': ruoli
    }