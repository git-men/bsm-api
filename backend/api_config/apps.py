from django.apps import AppConfig
from django.conf import settings
from api_core.api import const
from .api import js_driver


class ApiConfigConfig(AppConfig):
    name = 'api_config'

    def ready(self):
        api_driver = getattr(settings, 'API_DRIVER', const.DEFALUT_DRIVER)
        if api_driver == const.DRIVER_JS:
            js_driver.load_api_js()
