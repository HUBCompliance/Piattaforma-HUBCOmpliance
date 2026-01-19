from django import template

register = template.Library()  # Questa riga è obbligatoria

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def total_questions(domande_dict):
    return sum(queryset.count() for queryset in domande_dict.values())
@register.filter
def get_item(dictionary, key):
    # Se per qualche motivo dictionary non è un dizionario, restituisci None invece di crashare
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(key)