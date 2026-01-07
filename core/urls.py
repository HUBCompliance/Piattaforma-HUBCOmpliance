from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # --- AMMINISTRAZIONE ---
    path('admin/', admin.site.urls),

    # --- INTERNAZIONALIZZAZIONE (Lingua) ---
    path('i18n/', include('django.conf.urls.i18n')),

    # --- APP DEL PROGETTO (Moduli Verticali) ---
    path('courses/', include('courses.urls')),
    path('compliance/', include('compliance.urls')),
    
    # --- NUOVO MODULO DI MONITORAGGIO (NIS2 Detection) ---
    # Gestisce il semaforo tecnico e il polling verso Prometheus
    path('monitoring/', include('monitoring.urls')),

    # --- APP USER_AUTH (Gestione Utenti e Dashboard Studente) ---
    # Includiamo le rotte alla radice per gestire la home page
    path('', include('user_auth.urls')),

    # --- REDIRECT DI SICUREZZA ---
    path('auth/', include('user_auth.urls')),
]

# --- GESTIONE FILE MEDIA E STATICI IN LOCALE (DEBUG) ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)