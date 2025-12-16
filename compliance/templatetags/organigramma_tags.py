from django import template

# Registra la libreria di tag/filtri
register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Ritorna il valore per una data chiave da un dizionario o un attributo per nome da un oggetto.
    Usato per accedere ai campi di un BoundField in un Formset.
    """
    try:
        # 1. Tenta l'accesso come elemento (es. per dizionari)
        return dictionary[key]
    except (TypeError, IndexError, KeyError):
        try:
            # 2. Tenta l'accesso come attributo (es. per BoundField)
            return getattr(dictionary, key)
        except AttributeError:
            # 3. Fallback per .get()
            return dictionary.get(key)
        except Exception:
            return None

@register.filter
def get_ruoli_by_type(azienda, ruolo_tipo):
    """
    Ritorna il primo RuoloPrivacy associato all'azienda per un dato ruolo_tipo.
    Si assume che l'oggetto 'azienda' abbia una relazione inversa chiamata 'ruoloprivacy_set'
    che punta ai modelli di RuoloPrivacy.
    """
    try:
        # Filtra i ruoli per l'azienda data e il tipo specificato, prendendo il primo risultato.
        # Questa riga risolve il TemplateSyntaxError.
        return azienda.ruoloprivacy_set.filter(ruolo_tipo=ruolo_tipo).first()
    except AttributeError:
        # Ritorna None se l'oggetto azienda non è valido o manca la relazione
        return None