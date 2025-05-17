from django.apps import AppConfig


class MedConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'med'

    def ready(self):
        import med.signals