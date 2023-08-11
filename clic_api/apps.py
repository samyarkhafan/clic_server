from django.apps import AppConfig


class ClicApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clic_api'
    def ready(self):
        from . import signals