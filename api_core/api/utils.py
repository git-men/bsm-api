import json
from django.conf import settings
from api_basebone.core import exceptions

from . import const
from api_db.api import db_driver
from api_config.api import js_driver


def query_from_json(data, key):
    """
    data为一组json格式的数据，可以是数组也可以是字典
    key是字符串，以点分隔，每一点深入一层
    """
    if isinstance(key, str):
        keys = key.split('.')

    cur = data
    for k in keys:
        if isinstance(k, dict):
            cur = cur[k]
        elif isinstance(k, list):
            cur = [d[k] for d in cur]
        else:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR, error_data=f'找不到{key}'
            )
    return cur


def del_exclude_keys(config, exclude_keys):
    if not config:
        return
    for k in exclude_keys:
        if k in config:
            del config[k]


def format_api_config(api_config):
    api_config['displayfield'] = [f['name'] for f in api_config['displayfield']]
    # setfield = []
    for f in api_config['setfield']:
        # value = f['value']
        if isinstance(f['value'], str):
            try:
                f['value'] = json.loads(f['value'])
            except Exception:
                pass
        # setfield.append([f['name'], value])
    # api_config['setfield'] = setfield

    if api_config['ordering']:
        api_config['ordering'] = api_config['ordering'].replace(' ', '').split(',')
    else:
        api_config['ordering'] = []

    if api_config['expand_fields']:
        api_config['expand_fields'] = (
            api_config['expand_fields'].replace(' ', '').split(',')
        )
    else:
        api_config['expand_fields'] = []

    format_param_config(api_config['parameter'])
    format_filter_config(api_config['filter'])
    format_set_field_config(api_config['setfield'])
    if ('permission' in api_config) and api_config['permission']:
        format_permission_config(api_config['permission'])
    else:
        api_config['permission'] = {'group': []}


def format_param_config(params):
    exclude_keys = ['id', 'api', 'layer', 'parent', 'use_default']
    for param in params:
        if param['use_default'] is False:
            del param['default']

        if 'default' in param and isinstance(param['default'], str):
            try:
                param['default'] = json.loads(param['default'])
            except Exception:
                pass

        if 'children' in param:
            if param['children']:
                format_param_config(param['children'])
            else:
                del param['children']

        del_exclude_keys(param, exclude_keys)


def format_filter_config(filters):
    if not filters:
        return

    for f in filters:
        exclude_keys = ['id', 'api', 'layer', 'parent', 'type']
        if f['type'] == const.FILTER_TYPE_CONTAINER:
            exclude_keys.extend(['field', 'value'])
        else:
            exclude_keys.extend(['children'])

        del_exclude_keys(f, exclude_keys)

        if 'children' in f:
            format_filter_config(f['children'])

        if 'value' in f and isinstance(f['value'], str):
            # value = f['value']
            try:
                f['value'] = json.loads(f['value'])
            except Exception:
                pass


def format_set_field_config(fields):
    exclude_keys = ['id', 'api', 'layer', 'parent']
    for f in fields:
        del_exclude_keys(f, exclude_keys)

        if 'children' in f:
            if f['children']:
                format_set_field_config(f['children'])
            else:
                del f['children']


def format_permission_config(permission):
    exclude_keys = ['display_name']
    del_exclude_keys(permission, exclude_keys)

    if 'group' in permission:
        permission['group'] = [g['id'] for g in permission['group']]


def get_api_driver():
    """依据setting配置返回相应的api驱动模块，例如JS为json配置文件，db为数据库"""
    api_driver = getattr(settings, 'API_DRIVER', const.DEFALUT_DRIVER)
    api_driver = api_driver.lower()
    if api_driver == const.DRIVER_DB:
        return db_driver
    elif api_driver == const.DRIVER_JS:
        return js_driver
    else:
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'api存储驱动参数\'API_DRIVER\'配置不正确',
        )
