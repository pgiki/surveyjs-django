from django.apps import AppConfig


class Config(AppConfig):
    name = "core"

    def ready(self):
        from . import signals  # NOQA
