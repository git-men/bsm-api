from django.apps import AppConfig


class TriggerCoreConfig(AppConfig):
    name = 'trigger_core'

    def ready(self):
        from api_basebone.restful.client.views import register_api
        from .bsm.api import exposed
        from .bsm import functions  # 注册所有云函数

        register_api(self.name, exposed)
        from . import signals
