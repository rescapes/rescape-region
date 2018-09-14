"""
Django settings for the package. This is used to create migrations and run tests. It is not part of the build package
"""

import os

TEST_RUNNER = 'snapshottest.django.TestRunner'

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ENV
PROD = os.environ.get('ENV_TYPE') == 'prod'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'dp&=7jt@y*^3kwfxh&!xufl9pu$!!t2vhvxozgf5y$xd(*(7w*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = 'true' == (os.environ.get('DJANGO_DEBUG', 'true')).lower()

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'rest_framework',
    'rescape_region'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # After django.contrib.auth.middleware.AuthenticationMiddleware...
    'graphql_jwt.middleware.JSONWebTokenMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'testdb',
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

CACHES = {

    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    },
    'db': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'db_cache',
    }
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',)
}

LOG_PATH = os.path.join(BASE_DIR, "log/")
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s]- %(message)s'}

    },
    'handlers': {
        'django_error': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_PATH, "django_error.log"),
            'formatter': 'standard'
        },
        'django_info': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_PATH, "django_info.log"),
            'formatter': 'standard'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        }
    },
    'loggers': {
        'info': {
            # Use for custom log info: logger = logging.getLogger("info")
            'handlers': ['django_info', 'console'],
            'propagate': True,
            'level': 'INFO',
        },
        'django': {
            # Requests only go to the console, don't log to file
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            # DB interactions only log warnings or greater to error file
            'level': 'WARNING',
            'handlers': ['django_error', 'console'],
        },
        'django.request': {
            # Request errors log to error file
            'handlers': ['django_error', 'console'],
            'level': 'WARNING',
            'propagate': True
        },
        'graphene': {
            'handlers': ['django_info', 'console'],
            'propagate': True,
            'level': 'INFO',
        },
        'graphql': {
            'handlers': ['django_info', 'console'],
            'propagate': True,
            'level': 'INFO',
        },
        'rescape_graphene': {
            'handlers': ['django_info', 'console'],
            'propagate': True,
            'level': 'DEBUG',
        }
    },
}


AUTHENTICATION_BACKENDS = [
    'graphql_jwt.backends.JSONWebTokenBackend',
    'django.contrib.auth.backends.ModelBackend',
]

GRAPHENE = {
    'SCHEMA': 'sample_schema',
    'MIDDLEWARE': [
        'graphene_django.debug.DjangoDebugMiddleware',
    ]
}