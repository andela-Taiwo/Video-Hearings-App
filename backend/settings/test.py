import sys
from settings.base import *


DATABASES["default"] = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": "mydatabase",
}

# Logging configuration for tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['null'],
            'propagate': False,
        },
        'redis': {
            'handlers': ['null'],
            'propagate': False,
        },
    },
}