from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
# Importiamo la nostra vista personalizzata per il debug delle email
from user_auth.views import CustomPasswordResetView 

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- GESTIONE LINGUA (Mancava questa) ---
    path('i18n/', include('django.conf.urls.i18n')),
    # ----------------------------------------

    # --- GESTIONE PASSWORD RESET (Override) ---
    # Usiamo la nostra CustomPasswordResetView invece di quella standard di Django
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    
    # Le altre viste del flusso di reset rimangono quelle standard di Django
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    # ------------------------------------------

    # --- APP DEL PROGETTO ---
    path('', include('user_auth.urls')),
    path('courses/', include('courses.urls')),
    path('compliance/', include('compliance.urls')),
]

# --- SERVIRE FILE MEDIA IN DEBUG (LOCALE) ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)