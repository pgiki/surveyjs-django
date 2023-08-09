from django.apps import AppConfig


class Config(AppConfig):
    name = "surveyjs"

    def ready(self):
        from . import signals  # NOQA
