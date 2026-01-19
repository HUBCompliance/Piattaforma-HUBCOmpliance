from django.urls import path, include
from . import views
from .views import CustomPasswordResetView

urlpatterns = [
    # AUTH STANDARD (login, logout, register, etc.)
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # DASHBOARDS E PROFILI
    # Questa è la vista root ('/') che gestisce lo smistamento dei ruoli
    # Nota: Abbiamo riutilizzato 'dashboard_studente' come nome della vista per l'URL radice ('/')
    path('dashboard_studente/', views.dashboard_studente, name='dashboard_studente'),
    # === CORREZIONE DEL ROUTING PROFILO ===
    # Mappiamo l'URL '/profilo/' al nuovo nome della funzione: 'profilo_utente'.
    # Usiamo il nome URL generico 'profilo_utente' (come mappato in core/urls.py)
    path('profilo/', views.profilo_utente, name='profilo_utente'),

    # Rimuoviamo la mappatura 'profilo_studente' e 'profilo_update' per evitare conflitti e puntiamo all'unica vista.
    # L'URL /profilo/modifica/ è ora gestito all'interno della vista profil_utente tramite POST.
    # path('profilo/modifica/', views.profilo_update, name='profilo_update'), # RIMOZIONE

   # PASSWORD RESET (Customizzato - Allineato agli standard Django per i nomi)
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    # Qui usiamo il trattino nel nome per matchare il template mail
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # REPORTING ADMIN
    path('admin/export-excel-aziende/', views.export_aziende_excel, name='export_aziende_excel'),
]