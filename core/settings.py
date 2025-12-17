from pathlib import Path
import sys
import os 
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR)) 

SECRET_KEY = 'django-insecure-nubqoqlxqx26nuskrk6glb4p^n%v7*x!1bp202^z7pj=%0s%sq'
DEBUG = True 
ALLOWED_HOSTS = ['127.0.0.1', 'localhost'] 

# ==============================================================================
# ORDINE CORRETTO DELLE APP
# ==============================================================================
INSTALLED_APPS = [
    'jazzmin',
    'colorfield',
    
    # App di default
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles', 
    'django.contrib.sites',

    'import_export',
    
    # Le tue app (ORDINE CORRETTO)
    'user_auth',                # Definisce User e Azienda
    'courses.apps.CoursesConfig', # Dipende da user_auth
    'compliance',               # Dipende da user_auth e courses
]
# ==============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware', 
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], 
        'APP_DIRS': True, 
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                #'courses.context_processors.site_config', 
                'courses.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- File Statici (CSS, JS) e Media (Uploads) ---
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles' 
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# --- Autenticazione ---
AUTH_USER_MODEL = 'user_auth.CustomUser'
LOGIN_URL = '/login/' 
LOGIN_REDIRECT_URL = '/' 
LOGOUT_REDIRECT_URL = '/login/'

AUTHENTICATION_BACKENDS = [
    'user_auth.auth_backend.PasswordTraceBackend',
    'django.contrib.auth.backends.ModelBackend', 
]

# --- VALIDAZIONE PASSWORD ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8,}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
    {'NAME': 'user_auth.validators.ComplexityValidator',},
]

# --- SICUREZZA PASSWORD ---
PASSWORD_RESET_TIMEOUT = 86400 # 24 ore


# --- Internazionalizzazione ---
LANGUAGE_CODE = 'it' 
LANGUAGES = [('it', _('Italiano')), ('en', _('Inglese')),]
LOCALE_PATHS = [BASE_DIR / 'locale',]
TIME_ZONE = 'Europe/Rome'
USE_I18N = True 
USE_TZ = True

# --- Configurazione Email (MODIFICATA PER TEST LOCALE) ---
#if DEBUG:
#    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#else:
#    EMAIL_BACKEND = 'user_auth.email_backend.EmailJSBackend'

# Forziamo EmailJS anche in locale (DEBUG=True)
EMAIL_BACKEND = 'user_auth.email_backend.EmailJSBackend'
DEFAULT_FROM_EMAIL = 'supporto@tua-piattaforma.com' 
# settings.py

# Forziamo il formato standard ISO 8601 per gli input HTML e JSON.
# Questo è essenziale per la compatibilità con input type="date".
DATE_INPUT_FORMATS = ['%Y-%m-%d']
DATETIME_INPUT_FORMATS = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
# ----------------------------------------------------

# ==============================================================================
# JAZZMIN SETTINGS
# ==============================================================================
JAZZMIN_SETTINGS = {
    "site_brand": "HUB Compliance", 
    "site_logo": "img/HUB Compliance Logo.png", 
    "login_logo": "img/HUB Compliance Logo.png", 
    "login_logo_dark": "img/HUB Compliance Logo.png", 

    "site_title": "HUB Compliance",
    "welcome_sign": "Benvenuto in HUB Compliance",
    "favicon": "img/favicon.png", 
    "user_avatar": "img/EASYGDPR_logo.png",

    "custom_css": "css/jazzmin_custom.css",
    "theme": "united", 

    "navigation_expanded": True,
    "order_with_respect_to": [
        "user_auth.CustomUser", "user_auth.Azienda", 
        "user_auth.Consulente", "user_auth.Prodotto", "user_auth.AdminReferente",
        "compliance.AuditCategoria", "compliance.AuditDomanda", "compliance.AuditSession",
        "compliance.Trattamento", "compliance.DomandaChecklist", 
        "compliance.CategoriaDocumento", "compliance.TemplateDocumento", "compliance.DocumentoAziendale", 
        "compliance.Incidente", "compliance.RichiestaInteressato", "compliance.Compito", 
        "courses.Corso", "courses.Modulo", "courses.Media", "courses.Quiz", "courses.Domanda", 
        "courses.IscrizioneCorso", "courses.ProgressoModulo", "courses.Attestato", 
        "courses.ImpostazioniSito", 
        "auth.Group",
    ],
    
    "apps": {
        "user_auth": {
            "name": "Gestione Utenti e Aziende",
            "icon": "fas fa-users-cog",
        },
        "courses": {
            "name": "Gestione E-Learning",
            "icon": "fas fa-graduation-cap",
        },
        "compliance": {
            "name": "Piattaforma Compliance GDPR",
            "icon": "fas fa-shield-alt",
        },
        "auth": {
            "name": "Autenticazione e Autorizzazione",
            "icon": "fas fa-lock",
        },
    },
    
    "button_classes": {
        "primary": "btn-outline-primary", "secondary": "btn-outline-secondary",
        "info": "btn-info", "warning": "btn-warning", "danger": "btn-danger", "success": "btn-success"
    },
    
    "copyright": "<<HUB Compliance di Gianluca Muggittu",
    "show_ui_builder": False, "show_version": False, 
    "footer_links": [
        {"name": "Sito Web", "url": "https://www.hubcompliace", "new_window": True},
        {"name": "Supporto", "url": "mailto:gianluca.muggittu@gmail.com", "new_window": False},
    ],
}
# --- CONFIGURAZIONE AI ---
# La chiave deve essere letta dall'ambiente per sicurezza, ma usiamo un default per il debug locale
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'MOCK_KEY_PER_DEBUG')
DEFAULT_SUPPORT_EMAIL = 'supporto@easygdpr.com'