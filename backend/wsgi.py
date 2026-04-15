"""
WSGI config for backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

import django
from django.apps import apps
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

if not apps.ready:
    django.setup()

if os.getenv("RUN_MIGRATIONS_ON_STARTUP", "true").strip().lower() in {"1", "true", "yes", "on"}:
    call_command("migrate", interactive=False, verbosity=0)

application = get_wsgi_application()
