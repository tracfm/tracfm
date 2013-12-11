# Django settings for the trac fm project.
import os
PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
# ('Your Name', 'your_email@example.com'),
)

ROUTER_PASSWORD = "nyarukatrac"

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'tracfm',
        'USER': 'tracfm',
        'PASSWORD': 'tracfm',
        'HOST': '',
        'PORT': '',
        #'OPTIONS': {
        #    "init_command": "SET storage_engine=INNODB",
        #    }
        }
}


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Africa/Kampala'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = 'media'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = 'sitestatic'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/sitestatic/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = STATIC_URL + "admin/"


# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'y801-+3@wm#82ev*dnoh07jl(-di(hl1$pudp6vwmgr5pnnu69'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
    )

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
    )

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'tracfm.middleware.AjaxRedirect',
    'smartmin.users.middleware.ChangePasswordMiddleware',
    )

ROOT_URLCONF = 'tracfm.urls'

TEMPLATE_DIRS = (

)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
            },
        }
}

#================================================================================================
# Trac configuration
#================================================================================================

import os

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.markup',

    # mo-betta permission management
    'guardian',

    # the django admin that does suck
    'django.contrib.admin',

    # gunicorn
    'gunicorn',

    # rapidsms FTW!
    'rapidsms',
    'rapidsms_httprouter',

    # async tasks,
    'djcelery',

    # compress css and js
    'compressor',

    'util',

    # smartmin
    'smartmin',

    # nsms + plus
    'nsms',
    'nsms_plus',

    # users
    'smartmin.users',
    'trac_users',

    # quickblocks
    'django_quickblocks',
    'django_quickblocks.stories',

    # simple_locations
    'mptt',
    'code_generator',
    'simple_locations',

    # humanize
    'django.contrib.humanize',

    # our locations
    'locations',

    # messages
    'messages',

    # and our polls
    'polls',

    # easy thumbnails
    'sorl.thumbnail',

    # south migrations
    'south',
)

SMS_APPS = ('polls',)
RAPIDSMS_TABS = []

# debug tool bar needs this
INTERNAL_IPS = ('127.0.0.1',)

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS' :False,
    }

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/users/login/"
LOGOUT_REDIRECT_URL = "/"

#-----------------------------------------------------------------------------------
# Directory Configuration
#-----------------------------------------------------------------------------------

PROJECT_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)))

FIXTURE_DIRS = (os.path.join(PROJECT_DIR, '../fixtures'),)
TEMPLATE_DIRS = (os.path.join(PROJECT_DIR, '../templates'),)
STATICFILES_DIRS = (os.path.join(PROJECT_DIR, '../static'),)
STATIC_ROOT = os.path.join(PROJECT_DIR, '../sitestatic')
MEDIA_ROOT = os.path.join(PROJECT_DIR, '../media')

#-----------------------------------------------------------------------------------
# Permission Management
#-----------------------------------------------------------------------------------

# this lets us easily create new permissions across our objects
PERMISSIONS = {
    '*': ('create', # can create an object
          'read',   # can read an object, viewing it's details
          'update', # can update an object
          'delete', # can delete an object,
          'list'),  # can view a list of the objects
    'rapidsms_httprouter.message': ('send',),
    'polls.pollcategoryset': ('public',),
    'polls.poll': ('public', 'recent', 'iframe','all', 'demographic'),
    'django_quickblocks.quickblock': ('html',)
}

# assigns the permissions that each group should have
GROUP_PERMISSIONS = {
    "Radio Hosts": ('polls.poll_create', 'polls.poll_update', 'polls.poll_read', 'polls.poll_list', 'polls.poll_delete', 
                    'polls.poll_recent', 'polls.poll_iframe', 'polls.poll_public',
                    'polls.pollcategoryset_read', 'polls.pollcategoryset_list', 'polls.pollcategoryset_create'),
    "Editors": ('polls.poll.*', 'polls.pollcategoryset.*', 'polls.pollcategory.*'),
    "Administrators": ('polls.poll.*', 'auth.user.*', 
                       'rapidsms_httprouter.message.*',
                       'django_quickblocks.quickblock.*', 'django_quickblocks.quickblockimage.*',
                       'simple_locations.areatype.*',
                       'locations.area.*',
                       'polls.pollcategoryset.*',
                       'polls.pollcategory.*',
                       'polls.respondent.*',
                       'polls.tracsettings.*',
                       'polls.demographicquestion.*',
                       'headers.header.*',)
}

#-----------------------------------------------------------------------------------
# Guardian Configuration
#-----------------------------------------------------------------------------------

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

# permissions for users that aren't logged in
ANONYMOUS_PERMISSIONS = (
)

ANONYMOUS_USER_ID = -1

#-----------------------------------------------------------------------------------
# Logging
#-----------------------------------------------------------------------------------

import logging
logging.basicConfig(
    level = logging.INFO,
    format = '[%(asctime)s] %(levelname)s %(message)s',
)

SENTRY_DSN = 'http://73633ae49a484d7882ca9560573c3062:54d493afc1424f83ab014f8266db07b2@monitor.nyaruka.com/7'


#-----------------------------------------------------------------------------------
# Our hostname
#-----------------------------------------------------------------------------------

HOSTNAME = 'www.trac.pro'

#-----------------------------------------------------------------------------------
# Redis Configuration
#-----------------------------------------------------------------------------------

import djcelery
djcelery.setup_loader()

CELERY_RESULT_BACKEND = 'database'

BROKER_BACKEND = 'redis'
BROKER_HOST = 'localhost'
BROKER_PORT = 6379
BROKER_VHOST = '8'

REDIS_PORT=6379
REDIS_HOST='localhost'
REDIS_DB=8

ROUTER_PASSWORD = 'nyarukatrac'

CACHES = {
    "default": {
        "BACKEND": "redis_cache.cache.RedisCache",
        "LOCATION": "localhost:6379:8",
        "OPTIONS": {
            "CLIENT_CLASS": "redis_cache.client.DefaultClient",
        }
    }
}

#-----------------------------------------------------------------------------------
# Crontab Settings 
#-----------------------------------------------------------------------------------

from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    "runs-every-five-minutes": {
        'task': 'rapidsms_httprouter.tasks.resend_errored_messages_task',
        'schedule': timedelta(minutes=5),
    },
}

#-----------------------------------------------------------------------------------
# Password Policies
#-----------------------------------------------------------------------------------

# after six failed login attempts, users are locked out
USER_FAILED_LOGIN_LIMIT = 6

# they are locked out permanently
USER_LOCKOUT_TIMEOUT = -1

# and cannot recover using email
USER_ALLOW_EMAIL_RECOVERY = False

# passwords expire after 60 days
USER_PASSWORD_EXPIRATION = 60

# and passwords must not be the same as one within one year
USER_PASSWORD_REPEAT_WINDOW = 365

