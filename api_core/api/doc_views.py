import json

from django.apps import apps
from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api_basebone.export.fields import get_model_field_config
from api_basebone.utils.meta import load_custom_admin_module
from . import const
from ..services import api_services

MODEL_TYPE_TO_SWAGGER = {
    'string': 'string',
    'text': 'string',
    'richtext': 'string',
    'integer': 'integer',
    'float': 'number',
    'decimal': 'number',
    'bool': 'boolean',
    'date': 'string',
    'time': 'string',
    'datetime': 'string',
    'image': 'string',
    'file': 'string',
}


API_PARAM_TYPE_TO_SWAGGER = {
    const.TYPE_STRING: 'string',
    const.TYPE_BOOLEAN: 'boolean',
    const.TYPE_INT: 'integer',
    const.TYPE_DECIMAL: 'number',
    const.TYPE_PK: 'string',
    const.TYPE_PAGE_IDX: 'integer',
    const.TYPE_PAGE_SIZE: 'integer',
    const.TYPE_JSON: 'string',
    const.TYPE_OBJECT: 'object',
}


class ApiDocViewSet(viewsets.GenericViewSet):
    '''读取配置接口'''

    def _load_bsm_admin_module(self):
        '''加载 bsm admin 模块'''
        load_custom_admin_module()

    def model_type_to_swagger(self, type):
        ''''''
        global MODEL_TYPE_TO_SWAGGER
        if type.lower() in MODEL_TYPE_TO_SWAGGER:
            return MODEL_TYPE_TO_SWAGGER[type]
        return 'string'

    def get_schema(self):
        '''获取 schema 配置'''
        schemas = {}
        models = api_services.get_api_schema_models()
        for model in models:
            field_configs = get_model_field_config(model)
            for model_name, d in field_configs.items():
                schema = {}
                schemas[model_name] = schema
                schema['type'] = 'object'
                required = []
                properties = {}
                schema['properties'] = properties
                for f in d['fields']:
                    p = {}
                    if 'type' in f:
                        if f['type'] == 'ref':
                            p['$ref'] = '#/components/schemas/' + f['ref']
                        elif f['type'] == 'mref':
                            p['type'] = 'array'
                            p['items'] = {}
                            p['items']['$ref'] = '#/components/schemas/' + f['ref']
                        else:
                            type = self.model_type_to_swagger(f['type'])
                            p['type'] = type
                    if 'displayName' in f:
                        p['description'] = f['displayName']
                    if 'required' in f and f['required']:
                        required.append(f['name'])
                    if 'default' in f:
                        p['default'] = f['default']
                    properties[f['name']] = p
                if required:
                    schema['required'] = required
        return schemas

    def get_params(self, api, parent=None):
        ''''''
        params = []
        if parent:
            param_config_list = parent.children
            params = {}
        else:
            param_config_list = api.parameter
            params = []
        global API_PARAM_TYPE_TO_SWAGGER
        for param_config in param_config_list:
            if param_config.type in API_PARAM_TYPE_TO_SWAGGER:
                type = API_PARAM_TYPE_TO_SWAGGER[param_config.type]
            else:
                type = 'string'

            if parent:
                name = param_config.name
                if param_config.is_array:
                    param = {'type': 'array', "items": {"type": type}}
                    if hasattr(param_config, 'children') and param_config.children:
                        param["items"]['properties'] = self.get_params(api, param_config)
                else:
                    param = {'type': type}
                    if hasattr(param_config, 'children') and param_config.children:
                        param['properties'] = self.get_params(api, param_config)
                params[name] = param
            else:
                param = {
                    'name': param_config.name,
                    'in': 'query',
                    'description': param_config.desc,
                    'required': param_config.required,
                    'style': 'form',
                }
                if param_config.is_array:
                    param['schema'] = {'type': 'array', "items": {"type": type}}
                    if hasattr(param_config, 'children') and param_config.children:
                        param['schema']["items"]['properties'] = self.get_params(
                            api, param_config
                        )
                else:
                    param['schema'] = {'type': type}
                    if hasattr(param_config, 'children') and param_config.children:
                        param['schema']['properties'] = self.get_params(api, param_config)

                params.append(param)
        return params

    def filter_display_fields(self, api, display_fields):
        display_fields_set = set()
        for field_str in display_fields:
            items = field_str.split('.')
            for i in range(len(items)):
                display_fields_set.add('.'.join(items[: i + 1]))

        result = {}
        model_class = apps.get_model(api.app, api.model)
        field_configs = get_model_field_config(model_class)
        result['type'] = 'object'
        result['properties'] = self.filter_sub_display_fields(
            display_fields_set, field_configs
        )
        return result

    def filter_sub_display_fields(self, display_fields_set, field_configs, prefix=''):
        if not field_configs:
            return {}
        properties = {}
        d = list(field_configs.values())[0]
        for f in d['fields']:
            name = f['name']
            if prefix:
                full_key = prefix + '.' + name
            else:
                full_key = name

            if full_key not in display_fields_set:
                continue

            p = {}
            if 'type' in f:
                if f['type'] in ('ref', 'mref'):
                    refs = f['ref'].split('__')
                    if len(refs) < 2:
                        continue
                    app = refs[0]
                    model_name = refs[1]
                    model_class = apps.get_model(app, model_name)
                    field_configs = get_model_field_config(model_class)
                    if f['type'] == 'ref':
                        p['type'] = 'object'
                        p['properties'] = self.filter_sub_display_fields(
                            display_fields_set, field_configs, full_key
                        )
                    elif f['type'] == 'mref':
                        p['type'] = 'array'
                        p['items'] = {'type': 'object'}
                        p['items']['properties'] = self.filter_sub_display_fields(
                            display_fields_set, field_configs, full_key
                        )
                else:
                    type = self.model_type_to_swagger(f['type'])
                    p['type'] = type
            if 'displayName' in f:
                p['description'] = f['displayName']
            if 'default' in f:
                p['default'] = f['default']
            properties[f['name']] = p

        return properties

    def get_response(self, api):
        ''''''
        response = {
            'schema': {
                'type': 'object',
                'properties': {
                    'error_code': {'type': 'integer'},
                    'error_message': {'type': 'string'},
                },
            }
        }

        model_name = f'{api.app}__{api.model}'
        result = {}
        if api.operation in (const.OPERATION_LIST,):
            display_fields = api.displayfield
            display_fields = [f.name for f in display_fields]
            result['type'] = 'array'
            if display_fields:
                result['items'] = self.filter_display_fields(api, display_fields)
            else:
                result['items'] = {'$ref': f'#/components/schemas/{model_name}'}
        elif api.operation in (
            const.OPERATION_RETRIEVE,
            const.OPERATION_CREATE,
            const.OPERATION_UPDATE,
            const.OPERATION_REPLACE,
        ):
            display_fields = api.displayfield
            display_fields = [f.name for f in display_fields]
            if display_fields:
                result = self.filter_display_fields(api, display_fields)
            else:
                result = {'$ref': f'#/components/schemas/{model_name}'}
        elif api.operation in (const.OPERATION_UPDATE_BY_CONDITION,):
            result = {'type': 'object', 'properties': {'count': {'type': 'integer'}}}
        elif api.operation in (const.OPERATION_DELETE_BY_CONDITION,):
            result = {'type': 'object', 'properties': {'deleted': {'type': 'integer'}}}
        elif api.operation in (const.OPERATION_FUNC,):
            if api.demo:
                try:
                    result = json.loads(api.demo)
                except:
                    pass  # 默认格式
        elif api.operation in (const.OPERATION_DELETE,):
            pass  # 默认格式
        else:
            pass  # 默认格式

        if result:
            response['schema']['properties']['result'] = result

        return response

    def get_paths(self):
        ''''''

        paths = {}
        for api in api_services.get_all_api_po():
            path = {}
            path['summary'] = api.summary
            path['operationId'] = api.slug
            path['parameters'] = self.get_params(api)
            response = self.get_response(api)
            path['responses'] = {
                '200': {
                    'description': 'successful operation',
                    'content': {'application/json': response},
                }
            }
            for method in api.method:
                slug = api.slug + '/' if not api.slug.endswith('/') else api.slug
                paths[f'/api/{slug}'] = {method: path}
        return paths

    @action(detail=False, url_path='doc')
    def doc(self, request, *args, **kwargs):
        ''''''
        result = {'openapi': '3.0.1', 'info': {'title': '闪电数据管理API', 'version': '1.0.0'}}
        result['paths'] = self.get_paths()
        result['components'] = {}
        result['components']['schemas'] = self.get_schema()
        return Response(result)

    @action(detail=False, url_path='help')
    def help(self, request, *args, **kwargs):
        ''''''
        context = {'static_url': '../static/api/swagger', 'doc_url': '../doc/'}
        return render(request, 'index.html', context)

