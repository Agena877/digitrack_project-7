"""
Django settings for DigiTrackProject project.
"""

import os
from pathlib import Path
import dj_database_url
from decouple import config

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security ---
SECRET_KEY = config('SECRET_KEY', default='django-insecure-vf!mpw5)q$6f(n*xex0jt!ic7n-=vt%e@na63ab)%g)!vy0091')
DEBUG = config('DEBUG', default=True, cast=bool)

# For Render deployment
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# --- Applications ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'DigiTrackProject.tourism',
]

# --- Middleware ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ✅ For static files on Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# --- URL & WSGI ---
ROOT_URLCONF = 'DigiTrackProject.DigiTrackProject.urls'
WSGI_APPLICATION = 'DigiTrackProject.DigiTrackProject.wsgi.application'

# --- Templates ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'tourism', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# --- Database ---
# ✅ Uses DATABASE_URL from Render environment variable
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default='postgresql://digitrack_user:12345@localhost:5432/digitrack_db'),
        conn_max_age=600
    )
}

# --- Password validation ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internationalization ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- Static files ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'tourism', 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- Default primary key field type ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Custom user model ---
AUTH_USER_MODEL = 'tourism.CustomUser'

# --- Optional: auto migrate when running locally ---
import sys
from django.core.management import execute_from_command_line
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DigiTrackProject.DigiTrackProject.settings")
    try:
        from django import setup
        setup()
    except ImportError:
        pass
    execute_from_command_line(sys.argv)
