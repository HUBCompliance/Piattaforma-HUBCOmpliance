from django.urls import path
from . import views
app_name = 'courses'

urlpatterns = [
    # Rotta principale del corso (quella che causava l'errore NoReverseMatch)
    path('corso/<int:course_id>/', views.dettaglio_corso, name='dettaglio_corso'),
    path('dashboard/registro-formazione/', views.registro_aziendale_view, name='registro_aziendale'),
    path('dashboard/registro-formazione/export/', views.esporta_registro_excel, name='esporta_registro_excel'),
    path('dashboard/registro-formazione/elimina/<int:voce_id>/', views.elimina_voce_registro, name='elimina_voce_registro'),
    
    # Rotta per completare il modulo (usata dal tasto nel template)
    path('modulo/completa/<int:modulo_id>/', views.completa_modulo, name='completa_modulo'),
    
    # Rotta per i quiz (usata dal tasto 'Inizia Quiz')
    path('quiz/<int:quiz_id>/', views.take_test, name='take_test'),
    
    # --- Generazione PDF Attestato ---
    path('attestato/<int:attestato_id>/pdf/', views.genera_attestato_pdf, name='genera_attestato_pdf'),
    
    # --- Servizi Cybersecurity ---
    path('consulente/avvia-scansione/<int:azienda_id>/', views.avvia_scansione_deashed, name='avvia_scansione_deashed'),
    path('analisi-dns/<int:azienda_id>/', views.analisi_dns_view, name='analisi_dns_view'),
]
