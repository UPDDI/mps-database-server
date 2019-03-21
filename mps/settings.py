# coding=utf-8
# Django settings for mps project.

import socket
import os

DEBUG = True
# TEMPLATE_DEBUG = DEBUG

ADMINS = ()

MANAGERS = ADMINS

try:
    # use our hidden credential file to import username and password info
    import mps_credentials

    postgresql_username = mps_credentials.postgresql_username
    postgresql_password = mps_credentials.postgresql_password
except ImportError:
    postgresql_username = ''
    postgresql_password = ''

if socket.gethostname() in 'prody':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            # Deprecated
            # 'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'mpsdb',
            'USER': postgresql_username,
            'PASSWORD': postgresql_password,
            'HOST': '127.0.0.1',
            'PORT': '',
        }
    }

else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            # Deprecated
            # 'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'mpsdb',
            'USER': 'mps',  # development DB username
            'PASSWORD': '4UhIg',  # development DB password
            'HOST': '127.0.0.1',
            'PORT': '',
        }
    }

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# ########
# PATHS #
#########

# Full filesystem path to the project.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Name of the directory for the project.
PROJECT_DIRNAME = PROJECT_ROOT.split(os.sep)[-1]

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'


# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, '..', STATIC_URL.strip("/"))


# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = "/media/"

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, '..', MEDIA_URL.strip("/"))


# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static'),
    os.path.join(PROJECT_ROOT, '../../mps-web-client/'),
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder'
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'f7e5f_n3toret66n=1oe0hm9c%*$lxd(_%4)$(k-pljt01^skk'
NEVERCACHE_KEY = 'x=scmcpvq_$-9pz3651h=ln0b#-x&%%hz_)u0uzghfwk6#++pl'

# List of callables that know how to import templates from various sources.
# TEMPLATE_LOADERS = (
#     'django.template.loaders.filesystem.Loader',
#     'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
# )

# OLD STYLE: REMOVED
# MIDDLEWARE_CLASSES = (
#     # 'debug_toolbar.middleware.DebugToolbarMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     # Uncomment the next line for simple clickjacking protection:
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
#     'django.middleware.security.SecurityMiddleware',
# )

# NEW STYLE
MIDDLEWARE = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'mps.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'mps.wsgi.application'

# TEMPLATE_DIRS = (
#     os.path.join(PROJECT_ROOT, 'templates'),
#     os.path.join(PROJECT_ROOT, '..', 'templates')
#     # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
#     # Always use forward slashes, even on Windows.
#     # Don't forget to use absolute paths, not relative paths.
# )

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # insert your TEMPLATE_DIRS here
            os.path.join(PROJECT_ROOT, 'templates'),
            os.path.join(PROJECT_ROOT, '..', 'templates')
        ],
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'mps.context_processors.google_analytics',
            ],
            'loaders': [
                # insert your TEMPLATE_LOADERS here
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                # REMOVED AS OF 2.0
                # 'django.template.loaders.eggs.Loader',
            ],
            # TECHNICALLY NOT NECESSARY
            'debug': DEBUG
        }
    },
]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.humanize',
    # South is not supported in Django >= 1.7
    # 'south',
    'django_extensions',

    # django debug toolbar
    'debug_toolbar',

    # django-import-export plugin
    'import_export',

    # Django REST Framework
    # http://www.django-rest-framework.org
    'rest_framework',

    # Comment out captchas for now
    # Django simple captchas
    'captcha',

    # Djangovoice for feedback
    'django_comments',
    'qhonuskan_votes',
    'djangovoice',

    # Haystack for searching
    'haystack',

    # MPS applications:
    'mps',
    'assays',
    'cellsamples',
    'compounds',
    'microdevices',
    'bioactivities',
    'drugtrials',
    'resources',
    'diseases',
    'compressor',

    'django_registration'
)

# Google Analytics ID
GOOGLE_ANALYTICS = ''

# Backend for username case insensitivity
AUTHENTICATION_BACKENDS = ('mps.backends.CaseInsensitiveModelBackend', )

# COMPRESSION
STATICFILES_FINDERS += (
    'compressor.finders.CompressorFinder',
)

COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
    'compressor.filters.template.TemplateFilter'
]

COMPRESS_JS_FILTERS = [
    'compressor.filters.jsmin.JSMinFilter',
]

# Whether or not to compress
COMPRESS_ENABLED = False
# Whether or not to use offline cache
COMPRESS_OFFLINE = True

# This should set all indices to use real time processing
# Users will have to pay the toll when adding or deleting indexed objects...
# This is disabled for the moment and a CRON job will be used for now
# HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

WHOOSH_INDEX = os.path.join(os.path.dirname(__file__), 'whoosh_index')

# For whoosh
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'mps.backends.ConfigurableWhooshEngine',
        'PATH': WHOOSH_INDEX,
        # can cause problems when dealing with data outside ascii
        # 'INCLUDE_SPELLING': True,
    },
}

# For elasticsearch
# HAYSTACK_CONNECTIONS = {
#     'default': {
#         'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
#         'URL': 'http://127.0.0.1:9200/',
#         'INDEX_NAME': 'haystack',
#     },
# }

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

LOGGING = {
    'version': 1,

    'disable_existing_loggers': False,

    'formatters': {

        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },

        'simple': {
            'format': '%(levelname)s %(message)s'
        },

    },

    'handlers': {
        'file_critical': {
            'level': 'CRITICAL',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.error.log',
            'formatter': 'verbose'
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.error.log',
            'formatter': 'verbose'
        },
        'file_warning': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.warning.log',
            'formatter': 'verbose'
        },
        'file_info': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.info.log',
            'formatter': 'verbose'
        },
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.debug.log',
            'formatter': 'verbose'
        },

    },

    'loggers': {

        'django': {
            'handlers': ['file_critical', 'file_error'],
            'propagate': True,
            'level': 'ERROR',
        },

        'mps': {
            'handlers': ['file_critical', 'file_error', 'file_info'],
            'propagate': True,
            'level': 'INFO',
        },

        'assays': {
            'handlers': ['file_error'],
            'level': 'ERROR',
        },

        'bioactivities': {
            'handlers': ['file_error'],
            'level': 'ERROR',
        },

        'cellsamples': {
            'handlers': ['file_error'],
            'level': 'ERROR',
        },

        'compounds': {
            'handlers': ['file_error'],
            'level': 'ERROR',
        },

        'drugtrials': {
            'handlers': ['file_error'],
            'level': 'ERROR',
        },

        'microdevices': {
            'handlers': ['file_error'],
            'level': 'ERROR',
        },

        'resources': {
            'handlers': ['file_error'],
            'level': 'ERROR',
        },

    }
}

# Database connection age limit in seconds
# Before Django 1.6 this was always ZERO
CONN_MAX_AGE = 6000

DEBUG_TOOLBAR_PATCH_SETTINGS = False

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'drf_ujson.renderers.UJSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'drf_ujson.parsers.UJSONParser',
    ),
    # Use hyperlinked styles by default.
    # Only used if the `serializer_class` attribute is not set on a view.
    'DEFAULT_MODEL_SERIALIZER_CLASS':
        'rest_framework.serializers.HyperlinkedModelSerializer',

    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}


def show_toolbar(request):
    return True

# I will need to tune this value
DATA_UPLOAD_MAX_NUMBER_FIELDS = 40000

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'mps.settings.show_toolbar'
}

# A test runner to run unit tests
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# This variable exists for the location of the validation starting column
TEMPLATE_VALIDATION_STARTING_COLUMN_INDEX = 52

# One-week activation window for registration
ACCOUNT_ACTIVATION_DAYS = 7

# Can be used to shutdown registration, if necessary
# REGISTRATION_OPEN = False

LOGIN_REDIRECT_URL = '/accounts/loggedin/'

# The console EmailBackend will post emails in the console
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = 'mps.backends.LoggingBackend'

DEFAULT_FROM_EMAIL = 'webmaster@localhost'
