# import importlib
import os
import json
import traceback

from django.conf import settings
from django.apps import apps

from django.core.management.base import BaseCommand
from ...driver.db_driver import driver

# from api_db.api import db_driver


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
        result['trigger'] = self.upload_trigger(app)
        for k, d in result.items():
            print('{} 上传：{}个成功，{}个异常'.format(k, d['success_num'], d['error_num']))

    def upload_trigger(self, app):
        self.stdout.write('上传 trigger 配置...')
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
                path = app_config.module.__path__[0] + '/trigger_config.json'
                if not os.path.isfile(path):
                    print(f"{app}没有API_CONFIGS")
                    continue
                with open(path, 'r', encoding='utf-8') as f:
                    s = f.read()
                    trigger_config_list = json.loads(s)
                print(f'-------------------开始上传 app：{app} 的trigger配置 ------------------')
                slug_list = []
                for config in trigger_config_list:
                    slug = ''
                    try:
                        slug = config['slug']
                        is_change = driver.save_trigger(config)
                        success_num += 1
                        if is_change:
                            change_num += 1
                        slug_list.append(slug)
                    except Exception as trigger_error:
                        error_num += 1
                        print(
                            f'trigger {slug} 异常:'
                            + str(trigger_error)
                            + ","
                            + traceback.format_exc()
                        )
                print(f'------------------- 上传 trigger 配置完成 ----------------------------')
                print(f'上传 trigger {app} 配置完成:{slug_list}')
                print()
            except Exception as e:
                print('上传 trigger 异常： {}'.format(str(e)))

        # print(f'{success_num}个API上传成功，{change_num}个变更，{error_num}个API 异常')
        return {'success_num': success_num, 'error_num': error_num}
