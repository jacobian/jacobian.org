import os
import dj_database_url
import urllib.parse


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET") or "dev-secret-s(p7%ue-l6r^&@y63p*ix*1"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.environ.get("DJANGO_DEBUG"))
INTERNAL_IPS = ("127.0.0.1",)

STAGING = bool(os.environ.get("STAGING"))

# Cloudflare details
CLOUDFLARE_EMAIL = os.environ.get("CLOUDFLARE_EMAIL", "")
CLOUDFLARE_TOKEN = os.environ.get("CLOUDFLARE_TOKEN", "")
CLOUDFLARE_ZONE_ID = os.environ.get("CLOUDFLARE_ZONE_ID", "")

# Google Analytics
GOOGLE_ANALYTICS_ID = os.environ.get("GOOGLE_ANALYTICS_ID")

# Application definition

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.redirects",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "micawber.contrib.mcdjango",
    "typogrify",
    "constance",
    "constance.backends.database",
    "blog",
    "feedstats",
    "speaking_portfolio",
)

MIDDLEWARE = (
    "django.contrib.redirects.middleware.RedirectFallbackMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)
if DEBUG:
    MIDDLEWARE = ("debug_toolbar.middleware.DebugToolbarMiddleware",) + MIDDLEWARE
    INSTALLED_APPS += ("debug_toolbar",)

# Sentry
SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN:
    INSTALLED_APPS += ("raven.contrib.django.raven_compat",)
    RAVEN_CONFIG = {
        "dsn": SENTRY_DSN,
        "release": os.environ.get("HEROKU_SLUG_COMMIT", ""),
        "environment": "staging" if STAGING else "production",
    }


ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates/")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "blog.context_processors.all",
            ]
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    "default": {"ENGINE": "django.db.backends.postgresql", "NAME": "simonwillisonblog"}
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_L10N = True
USE_TZ = True


if "DATABASE_URL" in os.environ:
    # Parse database configuration from $DATABASE_URL
    DATABASES["default"] = dj_database_url.config()

if "DISABLE_AUTOCOMMIT" in os.environ:
    DATABASES["default"]["AUTOCOMMIT"] = False

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Allow all host headers
ALLOWED_HOSTS = ["*"]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"

STATICFILES_DIRS = (os.path.join(BASE_DIR, "static/"),)

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


WHITENOISE_ROOT = os.path.abspath(os.path.join(STATICFILES_DIRS[0], "root-files"))

# urls.W002
# Your URL pattern '^/?archive/(\d{4})/(\d{2})/(\d{2})/$' has a regex beginning
# with a '/'. Remove this slash as it is unnecessary. If this pattern is
# targeted in an include(), ensure the include() pattern has a trailing '/'.
# This is deliberate (we get hits to //archive/ for some reason) so I'm
# silencing the warning:
SILENCED_SYSTEM_CHECKS = ("urls.W002",)


# Caching
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

REDIS_URL = os.environ.get("REDIS_URL")
if REDIS_URL:
    redis_url = urllib.parse.urlparse(REDIS_URL)
    CACHES["default"] = {
        "BACKEND": "redis_cache.RedisCache",
        "LOCATION": "{0}:{1}".format(redis_url.hostname, redis_url.port),
        "OPTIONS": {"PASSWORD": redis_url.password, "DB": 0},
        "VERSION": 2,
    }

SITE_ID = 1

PINBOARD_API_KEY = os.environ.get("PINBOARD_API_KEY", "")

CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_CONFIG = {
    "HOMEPAGE_NUM_ENTRIES": (5, "Number of blog entries on the home page"),
    "HOMEPAGE_NUM_ELSEWHERE": (7, "Number of 'elsewhere' links on the home page"),
    "HOMEPAGE_NUM_TALKS": (6, "Number of talks on the home page"),
}
if REDIS_URL:
    CONSTANCE_DATABASE_CACHE_BACKEND = "default"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "heroku": {
            "format": "source={name} level={levelname} message={message}",
            "style": "{",
        }
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "heroku"}},
    "loggers": {
        "": {"handlers": ["console"], "level": "INFO"},
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "micropub": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}

if "INDIEAUTH_BYPASS_SECRET" in os.environ:
    INDIEAUTH_BYPASS_SECRET = os.environ["INDIEAUTH_BYPASS_SECRET"]

# django-storages/s3 config
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", None)
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", None)
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", None)
AWS_DEFAULT_ACL = "public-read"
AWS_QUERYSTRING_AUTH = False
AWS_LOCATION = "jacobian-" + (
    "debug/" if DEBUG else ("staging/" if STAGING else "production/")
)

if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and AWS_STORAGE_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
