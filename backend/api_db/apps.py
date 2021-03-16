from django.apps import AppConfig


class ApiDbConfig(AppConfig):
    name = 'api_db'

    def ready(self):
        from api_basebone.restful.client.views import register_api
        from api_db.bsm.api import exposed, auth_exposed
        import api_db.bsm.functions  # 注册所有云函数
        import api_db.bsm.admin

        register_api(self.name, exposed)
        register_api('auth', auth_exposed)
        from . import signals

