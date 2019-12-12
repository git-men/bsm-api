from django.apps import AppConfig


class ApiDbConfig(AppConfig):
    name = 'api_db'

    def ready(self):
        from api_basebone.restful.client.views import register_api
        from api_db.bsm.api import exposed
        import api_db.bsm.functions  # 注册所有云函数

        register_api(self.name, exposed)
        from . import signals

