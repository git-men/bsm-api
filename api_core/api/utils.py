import json
from django.conf import settings
from api_basebone.core import exceptions

from . import const
from api_db.api import db_driver
from api_config.api import js_driver


def format_api_config(api_config):
    exclude_keys = ['id']
    for k in exclude_keys:
        if k in api_config:
            del api_config[k]

    api_config['displayfield'] = [f['name'] for f in api_config['displayfield']]
    # api_config['setfield'] = [[f['name'], f['value']] for f in api_config['setfield']]
    setfield = []
    for f in api_config['setfield']:
        value = f['value']
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except Exception as e:
                pass
        setfield.append([f['name'], value])
    api_config['setfield'] = setfield

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


def format_param_config(params):
    exclude_keys = ['id', 'api', 'layer', 'parent']
    for param in params:
        for ek in exclude_keys:
            if ek in param:
                del param[ek]

        if 'default' in param and isinstance(param['default'], str):
            try:
                param['default'] = json.loads(param['default'])
            except Exception as e:
                pass

        if 'children' in param:
            if param['children']:
                format_param_config(param['children'])
            else:
                del param['children']


def format_filter_config(filters):
    if not filters:
        return

    for f in filters:
        exclude_keys = ['id', 'api', 'layer', 'parent', 'type']
        if f['type'] == const.FILTER_TYPE_CONTAINER:
            exclude_keys.extend(['field', 'value'])
        else:
            exclude_keys.extend(['children'])

        for ek in exclude_keys:
            if ek in f:
                del f[ek]

        if 'children' in f:
            format_filter_config(f['children'])

        if 'value' in f and isinstance(f['value'], str):
            # value = f['value']
            try:
                f['value'] = json.loads(f['value'])
            except Exception as e:
                pass


def get_api_driver():
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
