import logging
import os
import sys
import json
import dj_database_url
import dotenv

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
consolehandler = logging.StreamHandler()
consolehandler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
consolehandler.setFormatter(formatter)
logger.addHandler(consolehandler)

from pathlib import Path
from dynaconf import Dynaconf
from dynaconf.validator import Validator

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    'x%#3&%giwv8f0+%r946en7z&d@9*rc$sl0qoql56xr%bh^w2mj',
)


if os.environ.get('DJANGO_DEBUG', default=False) in ['True', 'true', '1', True]:
    DEBUG = True
else:
    DEBUG = False


# Load env variables from file
dotenv_file = BASE_DIR / ".env"
if os.path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)

if not os.environ.get("ENV_FOR_DYNACONF"):
    logger.error(
        "Please provide ENV_FOR_DYNACONF \n"
        "Example of export ENV_FOR_DYNACONF=dev "
    )
    sys.exit(1)

settings = Dynaconf(
    envvar_prefix=False,
    environments=True,
    settings_files=["dynaconf.yaml"],
    validators=[
        Validator("ADMIN_IDS", must_exist=True),
        Validator("TELEGRAM_LOGS_CHAT_ID", must_exist=True),
        Validator("UPDATES_PATH", default="/updates"),
        Validator("WEBHOOK_DOMAIN", must_exist=True),
        Validator("YAML_FILE_PATH", default="strings"),
        Validator("LOG_DIR", default="logs"),
        Validator("LOG_FILE", default="logs.txt"),
        Validator("LOG_LEVEL", default="INFO"),
        Validator("MAX_SIZE_MB", default=10),
        Validator("DEFAULT_LANGUAGE", default="ru"),
        Validator("ALLOWED_LANGUAGES", default=["ru", "en"]),
        Validator("TIMESTAMP_FORMAT", default="%H:%M %d.%m.%Y"),
        Validator("TIME_ZONE", default="Europe/Moscow"),
        Validator("TELEGRAM_TOKEN", must_exist=True),
        Validator("DATABASE_URL", must_exist=True),
    ],
)
DATABASE_URL = settings.get("DATABASE_URL")
TELEGRAM_LOGS_CHAT_ID = settings.get("TELEGRAM_LOGS_CHAT_ID","") 

logger.info('====== ENV_FOR_DYNACONF: '+str(settings.get("ENV_FOR_DYNACONF","")))
logger.info('====== DATABASE_URL: '+str(settings.get("DATABASE_URL","")))
logger.info('====== DEBUG: '+str(DEBUG))

def get_plugins(Roles = ''):
    retpl = {}
    if Roles is None:
        return retpl
    plug = settings.get("PLUGINS")
    
    for pl in plug:
        pldict=dict(pl)
        for name_plug,val in pldict.items():
            #print('-1-',name_plug,Roles)
            if Roles:
               if not ("All" in Roles.split(',') or (name_plug in Roles.split(','))):
                   continue
            #print('-2-',name_plug)
            item = pldict.get(name_plug)
            ret = {}
            blocked=0
            if item:
                for it in item:
                    if ' = ' in it:
                        key = it.split(' = ')[0]
                        val = it.split(' = ')[1]
                    if key=='blocked' and val in ['True', 'true', '1', True]:
                        blocked=1
                    if key:
                        ret[key]=val
            if not blocked:
                retpl[name_plug] = ret
    return retpl


ALLOWED_HOSTS = ["*",]  # since Telegram uses a lot of IPs for webhooks

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 3rd party apps
    'django_celery_beat',
    'debug_toolbar',

    # local apps
    'users.apps.UsersConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',

    'django.middleware.common.CommonMiddleware',
]

INTERNAL_IPS = [
    # ...
    '127.0.0.1',
    # ...
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'dtb.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'dtb.wsgi.application'
ASGI_APPLICATION = 'dtb.asgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

#DATABASES = {    'default': dj_database_url.config(conn_max_age=600, default="sqlite:///db.sqlite3"),}
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL)
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images) 
# https://docs.djangoproject.com/en/3.0/howto/static-files/
#STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# https://stackoverflow.com/questions/63783517/django-heroku-raise-valueerrormissing-staticfiles-manifest-entry-for-s-c
# https://stackoverflow.com/questions/66533760/valueerror-missing-staticfiles-manifest-entry-on-heroku-with-docker-django-pip

WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ALLOW_ALL_ORIGINS = True

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')

# -----> CELERY
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379')
BROKER_URL = REDIS_URL
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_DEFAULT_QUEUE = 'default'

# -----> TELEGRAM
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN",settings.get("TELEGRAM_TOKEN",None))
if TELEGRAM_TOKEN is None:
    logging.error(
        "Please provide TELEGRAM_TOKEN in settings\settings.yaml.\n"
        "Example of .env file: https://github.com/ohld/django-telegram-bot/blob/main/.env_example"
    )
    sys.exit(1)

# -----> SENTRY
# import sentry_sdk
# from sentry_sdk.integrations.django import DjangoIntegration
# from sentry_sdk.integrations.celery import CeleryIntegration
# from sentry_sdk.integrations.redis import RedisIntegration

# sentry_sdk.init(
#     dsn="INPUT ...ingest.sentry.io/ LINK",
#     integrations=[
#         DjangoIntegration(),
#         CeleryIntegration(),
#         RedisIntegration(),
#     ],
#     traces_sample_rate=0.1,

#     # If you wish to associate users to errors (assuming you are using
#     # django.contrib.auth) you may enable sending PII data.
#     send_default_pii=True
# )
