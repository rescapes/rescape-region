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
    'django.contrib.staticfiles',
    'rest_framework',
    'safedelete',
    'graphene_django',
    'rescape_region'
]

STATIC_URL = '/static/'
STATIC_ROOT = 'staticfiles'
CORS_ORIGIN_ALLOW_ALL = True

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
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('SOP_DB_NAME', 'rescape_region'),
        'USER': os.environ.get('SOP_DB_USER', 'test_user'),
        'PASSWORD': os.environ.get('SOP_DB_PASS', 'test'),
        'HOST': os.environ.get('SOP_DB_HOST'),
        'PORT': os.environ.get('SOP_DB_PORT', ''),
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validator

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
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
}

ROOT_URLCONF = 'rescape_region.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'rescape_region/templates')],
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
    'SCHEMA': 'rescape_region.schema_models.schema.schema',
    'MIDDLEWARE': [
        # This messes up schema remote introspection
        #'graphene_django.debug.DjangoDebugMiddleware',
    ]
}
