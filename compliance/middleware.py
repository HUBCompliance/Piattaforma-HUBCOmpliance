import json
from user_auth.models import AuditLog

class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Esegue la richiesta e ottiene la risposta
        response = self.get_response(request)

        # Registriamo il log solo se l'utente è loggato e invia dati (POST)
        if request.user.is_authenticated and request.method == "POST":
            path = request.path
            
            # Saltiamo i log per componenti tecnici o statici
            if "admin/jsi18n" in path or "static" in path:
                return response

            azione = "UPDATE/CREATE"
            if "delete" in path.lower():
                azione = "DELETE"

            # Pulizia dati sensibili prima di salvare il log
            post_data = request.POST.copy()
            post_data.pop('csrfmiddlewaretoken', None)
            post_data.pop('password', None)
            
            # Creazione della descrizione (troncata a 500 caratteri)
            dati_string = json.dumps(post_data.dict())
            descrizione = f"URL: {path} | Data: {dati_string[:500]}"

            # Salvataggio nel database
            AuditLog.objects.create(
                utente=request.user,
                azione=azione,
                modello=path.split('/')[2] if len(path.split('/')) > 2 else "Generico",
                descrizione=descrizione,
                indirizzo_ip=self.get_client_ip(request)
            )

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip