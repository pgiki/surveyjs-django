"""
Django settings for surveys project.

For more information on this file, see
https://docs.djangoproject.com/

"""
import os
from pathlib import Path
from dotenv import load_dotenv
import yaml

load_dotenv()  # take environment variables from .env
IS_LOCAL = os.environ.get("IS_LOCAL")
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS=['http://*', 'https://*']
# Application definition
INSTALLED_APPS = [
   "admin_interface",
    "colorfield",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "reset_migrations",
    # permissions
    "guardian",
    "sorl.thumbnail",
    "django_seed",
    "import_export",
    "notifications",
    "django_extensions",
    "rest_framework_swagger",
    #
    "rest_framework",
    "django_filters",
    # for accounts registration
    "rest_framework.authtoken",
    "dj_rest_auth",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dj_rest_auth.registration",
    "corsheaders",
    # local apps
    "surveyjs.apps.Config",
    "core.apps.Config",
]



MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # for logging activity
    "request_logging.middleware.LoggingMiddleware",
    "django.middleware.locale.LocaleMiddleware",
]
# for guardian
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",  # default
    "guardian.backends.ObjectPermissionBackend",
)
ANONYMOUS_USER_NAME = 'nobody'
EVERYONE_GROUP_NAME = 'everyone'
APPEND_SLASH=False
SITE_ID=1

ROOT_URLCONF = 'surveys.urls'
ALLOWED_HOSTS = ["*"]
X_FRAME_OPTIONS = "SAMEORIGIN"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# SILENCED_SYSTEM_CHECKS = ["security.W019"]
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_ALL_ORIGINS = True # If this is used then `CORS_ALLOWED_ORIGINS` will not have any effect
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
] # If this is used, then not need to use `CORS_ALLOW_ALL_ORIGINS = True`

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates', ''],
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

WSGI_APPLICATION = 'surveys.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        # 'ENGINE':'django.contrib.gis.db.backends.postgis',
        "NAME": os.getenv("DATABASE_NAME"),
        "USER": os.getenv("DATABASE_USER"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD"),
        "HOST": os.getenv("DATABASE_HOST"),
        "PORT": os.getenv("DATABASE_PORT"),
    }
}

if os.getenv("IS_LOCAL"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
# REST FRAMEWORK
REST_AUTH_SERIALIZERS = {
    "USER_DETAILS_SERIALIZER": "core.serializers.UserSerializer",
    # will be hard migrating here due to having several versions of the app running multiple versions
    # "REGISTER_SERIALIZER":"core.serializers.UserSerializer",
}

REST_AUTH_REGISTER_SERIALIZERS = {
    "REGISTER_SERIALIZER": "core.serializers.UserSerializer",
}

REST_FRAMEWORK = {"DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema"}

REST_FRAMEWORK.update(
    {
        "COERCE_DECIMAL_TO_STRING": False,
        "DEFAULT_AUTHENTICATION_CLASSES": [
            'rest_framework.authentication.BasicAuthentication',
            "rest_framework.authentication.TokenAuthentication",
            "rest_framework.authentication.SessionAuthentication",
            # 'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        ],
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.IsAuthenticated",
        ],
        # 'EXCEPTION_HANDLER': 'activity_log.middleware.exceptionHandler',
        # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination', 0714769691
        "DEFAULT_PAGINATION_CLASS": "core.utils.pagination.CustomPagination",
        "PAGE_SIZE": 10,
        "DEFAULT_FILTER_BACKENDS": [  # TODO: Remove if changes to elastic search
            "django_filters.rest_framework.DjangoFilterBackend",
        ],
        "DEFAULT_RENDERER_CLASSES": [
            "rest_framework.renderers.JSONRenderer",
            "rest_framework.renderers.BrowsableAPIRenderer",
            "rest_framework.renderers.TemplateHTMLRenderer",
        ],
        "DEFAULT_PARSER_CLASSES": [
            "rest_framework.parsers.JSONParser",
            "rest_framework.parsers.FormParser",
            "rest_framework.parsers.MultiPartParser",
            # 'rest_framework.parsers.FileUploadParser',
        ],
    }
)


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "/static/"
LOCALE_PATHS = [
    os.path.join(BASE_DIR, "locale"),
]
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "surveyjs-react-client/static"),
]
# permissions configuration. Handy for setting default configurations when items are created for the first time
PERMISSIONS_SCHEMA_PATH = os.getenv('PERMISSIONS_SCHEMA_PATH')
PERMISSIONS_SCHEMA={}

if PERMISSIONS_SCHEMA_PATH:
    with open(PERMISSIONS_SCHEMA_PATH, "r") as stream:
        try:
            PERMISSIONS_SCHEMA = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)