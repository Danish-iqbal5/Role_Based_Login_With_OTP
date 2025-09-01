from django.apps import AppConfig

def ready(self):
    import permissions.signals

class PermissionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'permissions'
