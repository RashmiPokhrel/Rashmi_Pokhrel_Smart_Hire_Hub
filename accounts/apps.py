from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'

# apps.py

from django.apps import AppConfig

class HireConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hire'

    def ready(self):
        import accounts.signals
