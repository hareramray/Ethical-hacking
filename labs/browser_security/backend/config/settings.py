"""Deliberately small local lab; the experiment routes set their own CSP."""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("LAB_DATA_DIR", str(BASE_DIR / "data"))).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_DIR = BASE_DIR.parent / "frontend" / "dist"
LAB_ROLE = os.environ.get("LAB_ROLE", "main")
LAB_MAIN_ORIGIN = os.environ.get("LAB_MAIN_ORIGIN", "http://127.0.0.1:8766")
LAB_PEER_ORIGIN = os.environ.get("LAB_PEER_ORIGIN", "http://127.0.0.1:8767")

secret_file = DATA_DIR / ".secret-key"
try:
    with secret_file.open("x", encoding="ascii") as secret_stream:
        secret_stream.write(secrets.token_urlsafe(48))
except FileExistsError:
    pass
SECRET_KEY = secret_file.read_text(encoding="ascii").strip()
DEBUG = False
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "[::1]"]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
INSTALLED_APPS = ["django.contrib.contenttypes", "django.contrib.sessions", "securitylab"]
MIDDLEWARE = [
    "securitylab.middleware.LocalOnlyMiddleware",
    "securitylab.middleware.LabRoleMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "securitylab.middleware.ResponseHeadersMiddleware",
]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": DATA_DIR / "db.sqlite3"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
SESSION_COOKIE_NAME = "browser_lab_session"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_NAME = "browser_lab_csrf"
CSRF_COOKIE_SAMESITE = "Strict"
CSRF_FAILURE_VIEW = "securitylab.views.csrf_failure"
SESSION_COOKIE_AGE = 24 * 60 * 60
DATA_UPLOAD_MAX_MEMORY_SIZE = 80 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 64 * 1024
DATA_UPLOAD_MAX_NUMBER_FILES = 1
DATA_UPLOAD_MAX_NUMBER_FIELDS = 12
APPEND_SLASH = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "no-referrer"

# Query strings contain lab inputs; keep them out of the development access log.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "loggers": {"django.server": {"handlers": ["null"], "propagate": False}},
}
