from django.apps import AppConfig
from .api import js


class ApiConfigConfig(AppConfig):
    name = 'api_config'

    def ready(self):
        js.load_all_api_js()
