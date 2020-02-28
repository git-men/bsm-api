# import importlib
import os
import json
import traceback

from django.conf import settings
from django.apps import apps

from django.core.management.base import BaseCommand
from api_db.api import db_driver


class Command(BaseCommand):
    """输出模型配置

    只是简单的输出模型的配置，输出后的配置可进行调整和修改
    """

    def add_arguments(self, parser):
        """"""
        parser.add_argument('--app', type=str, help='上传api的app')

    def handle(self, *args, **kwargs):
        """"""
        app = kwargs.get('app')
        result = {}
        result['api'] = self.upload_api(app)
        for k, d in result.items():
            print('{} 上传：{}个成功，{}个异常'.format(k, d['success_num'], d['error_num']))

    def upload_api(self, app):
        self.stdout.write('上传 api 配置...')
        if app:
            export_apps = [app]
        else:
            export_apps = getattr(settings, 'API_APPS', None)
            export_apps = list(set(export_apps))

        error_num = 0
        success_num = 0
        change_num = 0
        for app in export_apps:
            try:
                app_config = apps.get_app_config(app)
                # module = app_config.module
                path = app_config.module.__path__[0] + '/api_config.json' if app not in settings.API_CONFIG_PATH else settings.API_CONFIG_PATH[app]
                if not os.path.isfile(path):
                    print(f"{app}没有API_CONFIGS")
                    continue
                with open(path, 'r', encoding='utf-8') as f:
                    s = f.read()
                    api_config_list = json.loads(s)
                print(f'-------------------开始上传 app：{app} 的api配置 ------------------')
                slug_list = []
                for config in api_config_list:
                    slug = ''
                    try:
                        slug = config['slug']
                        is_change = db_driver.save_api(config)
                        success_num += 1
                        if is_change:
                            change_num += 1
                        # print(f'loaded api：{slug},{is_change}')
                        slug_list.append(slug)
                    except Exception as api_error:
                        error_num += 1
                        print(
                            f'api {slug} 异常:'
                            + str(api_error)
                            + ","
                            + traceback.format_exc()
                        )
                print(f'------------------- 上传 api 配置完成 ----------------------------')
                print(f'上传 api {app} 配置完成:{slug_list}')
                print()
            except Exception as e:
                print('上传 API 异常： {}'.format(str(e)))

        # print(f'{success_num}个API上传成功，{change_num}个变更，{error_num}个API 异常')
        return {'success_num': success_num, 'error_num': error_num}
