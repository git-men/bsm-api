import logging
import json
import os
import traceback
import operator
from functools import reduce
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
            path = app_config.module.__path__[0] + '/api_config.json'
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


# TRIGGER_DATA[slug] = config
TRIGGER_DATA = {}
# TRIGGER_IDX[event] = [slug1,slug2...]
# TRIGGER_IDX = {}
# TRIGGER_LOAD_TIME {app:time}
TRIGGER_LOAD_TIME = {}


def load_trigger_data(config):
    global TRIGGER_DATA

    slug = config['slug']
    if slug not in TRIGGER_DATA:
        TRIGGER_DATA[slug] = {}


def load_trigger_js(app=None):
    if app:
        load_apps = [app]
    else:
        load_apps = getattr(settings, 'API_APPS', None)
        load_apps = list(set(load_apps))

    for app in load_apps:
        try:
            if app in TRIGGER_LOAD_TIME:
                now = timezone.now()
                delta = now - TRIGGER_LOAD_TIME[app]
                cache_time = getattr(settings, 'API_CACHE_TIME', 1 * 60)
                cache_time = int(cache_time)
                if delta.total_seconds() < cache_time:
                    """缓存时间未过"""
                    continue

            app_config = apps.get_app_config(app)
            path = app_config.module.__path__[0] + '/trigger_config.json'
            if not os.path.isfile(path):
                # print(f"{app}没有API_CONFIGS")
                continue
            with open(path, 'r', encoding='utf-8') as f:
                s = f.read()
                config_list = json.loads(s)

                # print(f'-------------------开始加载 app：{app} 的api配置 ------------------')
                slug_list = []
                for config in config_list:
                    slug = ''
                    try:
                        slug = config['slug']
                        load_trigger_data(app, config)
                        slug_list.append(slug)
                    except Exception as api_error:
                        print('导出 trigger {} 异常： {}'.format(slug, traceback.format_exc()))
                TRIGGER_LOAD_TIME[app] = timezone.now()
                # print(f'------------------- 加载 api 配置完成 ----------------------------')
                # print(f'加载 api {app} 配置完成:{slug_list}')
                # print()
        except Exception as e:
            print('加载 trigger 异常： {}'.format(str(e)))
            print()


def get_trigger_config(slug):
    load_trigger_js()
    return TRIGGER_DATA.get(slug)


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

    def get_trigger_config(self, slug):
        return get_trigger_config(slug)

    def list_trigger_config(self, event=None, *args, **kwargs):
        load_trigger_js()

        if event:
            ls = [d for d in TRIGGER_DATA.values() if d.get('event') == event]
        else:
            ls = TRIGGER_DATA.values()

        for k, v in kwargs:
            ls = [
                d
                for d in TRIGGER_DATA.values()
                if d.get('triggercondition', {}).get(k) == v
            ]

        return ls

    def add_trigger(self, config):
        raise exceptions.BusinessException(error_code=exceptions.CAN_NOT_SAVE_TRIGGER)

    def update_trigger(self, id, config):
        raise exceptions.BusinessException(error_code=exceptions.CAN_NOT_SAVE_TRIGGER)

    def save_trigger(self, config, id=None):
        raise exceptions.BusinessException(error_code=exceptions.CAN_NOT_SAVE_TRIGGER)


driver = JSDriver()
