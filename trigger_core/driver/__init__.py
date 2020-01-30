from django.conf import settings
from api_basebone.core import exceptions

from .. import const


class TriggerDriver:
    def get_trigger_config(self, slug):
        pass

    def get_trigger_config_by_id(self, id):
        pass

    def list_trigger_config(self, event=None, *args, **kwargs):
        pass

    def add_trigger(self, config):
        pass

    def update_trigger(self, id, config):
        pass

    def save_trigger(self, config, id=None):
        pass


def get_trigger_driver() -> TriggerDriver:
    """依据setting配置返回相应的TRIGGER驱动模块，例如JS为json配置文件，db为数据库"""
    api_driver = getattr(settings, 'API_DRIVER', const.DEFALUT_DRIVER)
    api_driver = api_driver.lower()
    if api_driver == const.DRIVER_DB:
        from . import db_driver

        return db_driver.driver
    elif api_driver == const.DRIVER_JS:
        from . import js_driver

        return js_driver.driver
    else:
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'触发器存储驱动参数\'TRIGGER_DRIVER\'配置不正确',
        )
