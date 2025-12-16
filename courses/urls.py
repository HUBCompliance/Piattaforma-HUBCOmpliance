from django.urls import path
from . import views

# Questa app al momento non ha viste pubbliche dedicate (tutto passa da user_auth o compliance),
# ma il file deve esistere per evitare errori di inclusione in core/urls.py.
# Se in futuro aggiungerai viste specifiche per i corsi (es. catalogo pubblico), le metterai qui.

urlpatterns = [
    # Lasciamo vuoto per ora, o aggiungiamo una vista placeholder se necessario.
    # Esempio futuro: path('', views.lista_corsi_pubblica, name='lista_corsi'),
    
    # --- Generazione PDF Attestato ---
    # Questa è l'unica vista "di servizio" che potrebbe stare qui
    path('attestato/<int:attestato_id>/pdf/', views.genera_attestato_pdf, name='genera_attestato_pdf'),
]