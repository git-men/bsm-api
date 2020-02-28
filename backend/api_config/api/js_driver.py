import logging
import json
import os
import traceback
from django.utils import timezone
from django.conf import settings
from django.apps import apps

from api_basebone.core import exceptions

from api_core.api.utils import APIDriver

log = logging.getLogger('django')

# API_DATA[app][slug]
API_DATA = {}
# API_LOAD_TIME {app:time}
API_LOAD_TIME = {}


def load_api_data(app, slug, config):
    global API_DATA

    if app not in API_DATA:
        API_DATA[app] = {}

    API_LOAD_TIME[app] = timezone.now()

    if 'slug' in config:
        slug = config['slug']
        API_DATA[app][slug] = config
        # log.info('加载 api：%s', config['slug'])


def load_api_js(app=None):
    if app:
        load_apps = [app]
    else:
        load_apps = getattr(settings, 'API_APPS', None)
        load_apps = list(set(load_apps))

    for app in load_apps:
        try:
            if app in API_LOAD_TIME:
                now = timezone.now()
                delta = now - API_LOAD_TIME[app]
                cache_time = getattr(settings, 'API_CACHE_TIME', 1 * 60)
                cache_time = int(cache_time)
                if delta.total_seconds() < cache_time:
                    """缓存时间未过"""
                    # print('cache not time out')
                    continue
                # else:
                #     print('cache time' + str(delta.total_seconds()))

            app_config = apps.get_app_config(app)
            path = app_config.module.__path__[0] + '/api_config.json' if app not in settings.API_CONFIG_PATH else settings.API_CONFIG_PATH[app]
            if not os.path.isfile(path):
                # print(f"{app}没有API_CONFIGS")
                continue
            with open(path, 'r', encoding='utf-8') as f:
                s = f.read()
                api_config_list = json.loads(s)

                # print(f'-------------------开始加载 app：{app} 的api配置 ------------------')
                slug_list = []
                for config in api_config_list:
                    slug = ''
                    try:
                        slug = config['slug']
                        load_api_data(app, slug, config)
                        slug_list.append(slug)
                    except Exception as api_error:
                        print('导出 API {} 异常： {}'.format(slug, traceback.format_exc()))
                # print(f'------------------- 加载 api 配置完成 ----------------------------')
                # print(f'加载 api {app} 配置完成:{slug_list}')
                # print()
        except Exception as e:
            print('加载 API 异常： {}'.format(str(e)))
            print()


class JSDriver(APIDriver):
    def add_api(self, config):
        raise exceptions.BusinessException(error_code=exceptions.CAN_NOT_SAVE_API)

    def update_api(self, id, config):
        raise exceptions.BusinessException(error_code=exceptions.CAN_NOT_SAVE_API)

    def save_api(self, config, id=None):
        raise exceptions.BusinessException(error_code=exceptions.CAN_NOT_SAVE_API)

    def get_api_config(self, slug, app=None):
        if app:
            load_api_js(app)
            apps = [app]
        else:
            load_api_js()
            global API_DATA
            apps = API_DATA.keys()

        for app in apps:
            if slug in API_DATA[app]:
                config = API_DATA[app][slug]
                return config

        return None

    def list_api_config(self, app=None):
        global API_DATA
        if app:
            apps = [app]
        else:
            apps = API_DATA.keys()
        results = []
        for app in apps:
            for slug in API_DATA[app].keys():
                r = self.get_api_config(slug, app)
            results.append(r)
            results.extend(API_DATA[app].values())

        return results


driver = JSDriver()
