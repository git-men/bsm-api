# import logging
import json
from django.db.models import Max
from django.db import transaction
from django.apps import apps

# from django.contrib.auth.models import Group

from api_basebone.core import exceptions

# from api_basebone.export.fields import get_model_field_config
from api_basebone.restful.serializers import multiple_create_serializer_class
from api_core.api.cache import api_cache
from api_core.api.cache import trigger_cache
from api_core.api import const
from api_core.api import utils

from api_db.models import Api, Parameter, DisplayField, SetField, Filter
from api_db.models import Trigger
from api_db.models import TriggerFilter
from api_db.models import TriggerAction
from api_db.models import TriggerActionSet
from api_db.models import TriggerActionFilter


def add_api(config):
    """新建API"""
    slug = config.get('slug', '')
    api = Api.objects.filter(slug=slug).first()
    if api:
        raise exceptions.BusinessException(error_code=exceptions.SLUG_EXISTS)

    save_api(config)


def update_api(id, config):
    """更新API"""
    save_api(config, id)


def save_api(config, id=None):
    """api配置信息保存到数据库"""
    with transaction.atomic():
        if id is None:
            slug = config.get('slug')
            api = Api.objects.filter(slug=slug).first()
            if not api:
                api = Api()
                api.slug = slug
                is_create = True
            else:
                is_create = False
        else:
            api = Api.objects.get(id=id)
            is_create = False
        api.config = str(config)
        api.app = config.get('app')
        api.model = config.get('model')
        try:
            model_class = apps.get_model(api.app, api.model)
        except LookupError:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'{api.app}__{api.model} 不是有效的model',
            )
        api.operation = config.get('operation')
        if api.operation not in const.OPERATIONS:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {api.operation} 不是合法的操作',
            )
        if 'name' in config:
            api.name = config['name']
        if 'summary' in config:
            api.summary = config['summary']
        if 'demo' in config:
            api.demo = config['demo']
        api.logined = config.get('logined', True)
        api.disable = config.get('disable', False)
        if 'ordering' in config:
            if isinstance(config['ordering'], list):
                api.ordering = ",".join(config['ordering'])
            else:
                api.ordering = config['ordering']
        if 'expand_fields' in config:
            if isinstance(config['expand_fields'], list):
                api.expand_fields = ",".join(config['expand_fields'])
            else:
                api.expand_fields = config['expand_fields']
        else:
            api.expand_fields = ''

        if 'func_name' in config:
            api.func_name = config['func_name']
        else:
            if api.operation == const.OPERATION_FUNC:
                """云函数api，却没有函数名"""
                raise exceptions.BusinessException(
                    error_code=exceptions.PARAMETER_FORMAT_ERROR,
                    error_data=f'\'operation\': {const.operation} 操作，必须有func_name函数名',
                )

        api.save()
        save_groups(api, config.get('groups'), is_create)

        param_list = save_parameters(api, config.get('parameter'), is_create)
        save_display_fields(api, config.get('displayfield'), is_create)
        save_set_fields(api, config.get('setfield'), is_create, model_class, param_list)
        save_filters(api, config.get('filter'), is_create)

        api_cache.delete_api_config(api.slug)

        return True


def save_parameters(api, parameters, is_create, parent=None):
    if (not parent) and (not is_create):
        Parameter.objects.filter(api__id=api.id).delete()

    if not parameters:
        return

    pk_count = 0
    model_list = []
    for param in parameters:
        param_type = param.get('type')
        if param_type not in const.TYPES:
            """未定义的参数类型"""
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'type\': {param_type} 不是合法的类型',
            )

        if (
            param_type in (const.TYPE_PAGE_SIZE, const.TYPE_PAGE_IDX)
            and api.operation != const.OPERATION_LIST
        ):
            """不是查询操作，不应该定义分页参数"""
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {api.operation} 操作不需要分页参数',
            )

        if param_type == const.TYPE_PK:
            if api.operation in (
                const.OPERATION_RETRIEVE,
                const.OPERATION_UPDATE,
                const.OPERATION_REPLACE,
                const.OPERATION_DELETE,
            ):
                pk_count += 1
            else:
                """修改、删除、详情以外的操作，不需要主键"""
                raise exceptions.BusinessException(
                    error_code=exceptions.PARAMETER_FORMAT_ERROR,
                    error_data=f'\'operation\': {api.operation} 操作不需要主键参数',
                )

        if parent and (param_type in const.SPECIAL_TYPES):
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data='复杂数据类型不允许包含主键、分页等特殊类型',
            )

        param_model = Parameter()
        param_model.api = api
        if parent:
            param_model.parent = parent
            param_model.layer = parent.layer + 1
        else:
            param_model.layer = 0
        param_model.name = param.get('name')
        param_model.desc = param.get('desc')
        param_model.type = param_type
        param_model.required = param.get('required')

        if 'is_array' in param:
            param_model.is_array = param.get('is_array')
        if 'default' in param:
            param_model.default = param.get('default')
            param_model.use_default = True
        else:
            param_model.default = None
            param_model.use_default = False

        param_model.save()
        if 'children' in param:
            save_parameters(api, param['children'], is_create, param_model)
        model_list.append(param_model)

    if (pk_count != 1) and api.operation in (
        const.OPERATION_RETRIEVE,
        const.OPERATION_UPDATE,
        const.OPERATION_REPLACE,
        const.OPERATION_DELETE,
    ):
        """修改、删除、详情，必须有主键"""
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'\'operation\': {api.operation} 操作有且只能有一个主键参数',
        )

    return model_list


def save_display_fields(api, fields, is_create):
    if not is_create:
        DisplayField.objects.filter(api__id=api.id).delete()

    if not fields:
        return

    if api.operation not in (
        const.OPERATION_LIST,
        const.OPERATION_RETRIEVE,
        const.OPERATION_CREATE,
        const.OPERATION_UPDATE,
        const.OPERATION_REPLACE,
    ):
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'\'operation\': {api.operation} 操作不需要display-fields',
        )

    for field in fields:
        field_model = DisplayField()
        field_model.api = api
        if isinstance(field, str):
            field_model.name = field
        elif isinstance(field, dict):
            field_model.name = field.get('name')
        else:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data='display-fields的格式不对',
            )
        field_model.save()


def save_set_fields(api, fields, is_create, model_class, param_list):
    if not is_create:
        SetField.objects.filter(api__id=api.id).delete()

    # if not fields:
    #     return

    if api.operation not in (
        const.OPERATION_CREATE,
        const.OPERATION_UPDATE,
        const.OPERATION_REPLACE,
        const.OPERATION_UPDATE_BY_CONDITION,
    ):
        if fields:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {api.operation} 操作不需要set-fields',
            )
        else:
            return

    if not fields:
        """如果没有设置set-fields，就默认和parameter配置一致"""
        fields = [
            p.to_set_field_config() for p in param_list if not p.is_special_defined()
        ]

    meta_filed_names = [f.name for f in model_class._meta.get_fields()]
    for field in fields:
        save_one_set_fields(api, field, meta_filed_names)


def save_one_set_fields(api, field, meta_filed_names, parent=None):
    field_model = SetField()
    field_model.api = api
    children = None
    if isinstance(field, list) and len(field) == 2:
        field_model.name = field[0]
        field_model.value = field[1]
    elif isinstance(field, dict):
        field_model.name = field.get('name')
        field_model.value = field.get('value')
        if 'children' in field:
            children = field['children']
    else:
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR, error_data='set-fields的格式不对'
        )

    if parent:
        field_model.layer = parent.layer + 1
        field_model.parent = parent
    else:
        if field_model.name not in meta_filed_names:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'{api.app}__{api.model} 没有属性{field_model.name}',
            )
        field_model.layer = 0
    field_model.save()

    if children:
        for f in children:
            save_one_set_fields(api, f, meta_filed_names, field_model)


def save_filters(api, filters, is_create):
    if not is_create:
        Filter.objects.filter(api__id=api.id).delete()

    if not filters:
        if api.operation in (
            const.OPERATION_DELETE_BY_CONDITION,
            const.OPERATION_UPDATE_BY_CONDITION,
        ):
            if api.operation == const.OPERATION_DELETE_BY_CONDITION:
                action = '删除'
            else:
                action = '更新'

            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {api.operation} 操作不允许无条件{action}，必须有filters条件',
            )
        return

    if api.operation not in (
        const.OPERATION_LIST,
        const.OPERATION_UPDATE_BY_CONDITION,
        const.OPERATION_DELETE_BY_CONDITION,
    ):
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'\'operation\': {api.operation} 操作不需要filters条件',
        )

    for filter in filters:
        save_one_filter(api, filter)


def save_one_filter(api, filter, parent=None):
    if 'children' in filter:
        filter_model = Filter()
        filter_model.api = api
        filter_model.type = const.FILTER_TYPE_CONTAINER
        if parent:
            filter_model.parent = parent
            filter_model.layer = parent.layer + 1
        else:
            filter_model.layer = 0
        filter_model.operator = filter.get('operator')
        filter_model.save()

        children = filter.get('children')
        for child in children:
            save_one_filter(api, child, filter_model)
    else:
        filter_model = Filter()
        filter_model.api = api
        filter_model.type = const.FILTER_TYPE_CHILD
        if parent:
            filter_model.parent = parent
            filter_model.layer = parent.layer + 1
        else:
            filter_model.layer = 0
        filter_model.field = filter.get('field')
        filter_model.operator = filter.get('operator')
        if 'value' in filter:
            filter_model.value = json.dumps(filter.get('value'))
        filter_model.save()


def save_groups(api: Api, groups, is_create):
    if groups is None:
        return
    api.groups.set(groups)
    api.save()


def get_api_config(slug):
    config = api_cache.get_api_config(slug)
    if config:
        config = json.loads(config)
        return config
    api = Api.objects.filter(slug=slug).first()
    if not api:
        raise exceptions.BusinessException(
            error_code=exceptions.OBJECT_NOT_FOUND, error_data=f'找不到对应的api：{slug}'
        )
    expand_fields = ['displayfield_set', 'permission', 'permission.group_set']
    exclude_fields = {
        # 'api_db__api': ['id'],
        'auth__permission': ['id', 'name', 'codename', 'content_type']
    }
    serializer_class = multiple_create_serializer_class(
        Api, expand_fields=expand_fields, exclude_fields=exclude_fields
    )
    serializer = serializer_class(api)
    config = serializer.data

    config['filter'] = get_filters_json(api)
    config['parameter'] = get_param_json(api)
    config['setfield'] = get_set_field_json(api)
    utils.format_api_config(config)
    api_cache.set_api_config(slug, json.dumps(config))
    return config


def queryset_to_json(queryset, expand_fields, exclude_fields):
    serializer_class = multiple_create_serializer_class(
        queryset.model, expand_fields=expand_fields, exclude_fields=exclude_fields
    )
    serializer = serializer_class(queryset, many=True)
    return serializer.data


def get_filters_json(api):
    max_layer = Filter.objects.filter(api__id=api.id).aggregate(max=Max('layer'))['max']
    max_layer = max_layer or 0
    exclude_fields = []
    expand_fields = []
    for i in range(max_layer):
        if i == 0:
            expand_fields.append('children')
        else:
            expand_fields.append(expand_fields[-1] + '.children')
    queryset = Filter.objects.filter(api__id=api.id, parent__isnull=True)
    return queryset_to_json(queryset, expand_fields, exclude_fields)


def get_param_json(api):
    max_layer = Parameter.objects.filter(api__id=api.id).aggregate(max=Max('layer'))[
        'max'
    ]
    max_layer = max_layer or 0
    exclude_fields = []
    expand_fields = []
    for i in range(max_layer):
        if i == 0:
            expand_fields.append('children')
        else:
            expand_fields.append(expand_fields[-1] + '.children')
    queryset = Parameter.objects.filter(api__id=api.id, parent__isnull=True)
    return queryset_to_json(queryset, expand_fields, exclude_fields)


def get_set_field_json(api):
    max_layer = SetField.objects.filter(api__id=api.id).aggregate(max=Max('layer'))['max']
    max_layer = max_layer or 0
    exclude_fields = []
    expand_fields = []
    for i in range(max_layer):
        if i == 0:
            expand_fields.append('children')
        else:
            expand_fields.append(expand_fields[-1] + '.children')
    queryset = SetField.objects.filter(api__id=api.id, parent__isnull=True)
    return queryset_to_json(queryset, expand_fields, exclude_fields)


def list_api_config(app=None):
    if app:
        apis = Api.objects.filter(app=app).values('slug').all()
    else:
        apis = Api.objects.values('slug').all()
    results = []
    for api in apis:
        r = get_api_config(api['slug'])
        results.append(r)

    return results


def get_trigger_config(slug):
    config = trigger_cache.get_config(slug)
    if config:
        config = json.loads(config)
        return config
    trigger = Trigger.objects.filter(slug=slug).first()
    if not trigger:
        raise exceptions.BusinessException(
            error_code=exceptions.OBJECT_NOT_FOUND, error_data=f'找不到对应的trigger：{slug}'
        )
    expand_fields = ['triggeraction_set', 'triggeraction_set.triggeractionset_set', 'triggerfilter_set',
        'triggeraction_set.triggeractionfilter_set']
    exclude_fields = {
        'api_db__triggeraction': ['id', 'trigger'],
        'api_db__triggeractionset': ['id', 'action'],
        'api_db__triggerfilter': ['id', 'trigger', 'layer'],
        'api_db__triggeractionfilter': ['id', 'action', 'layer'],
    }
    
    expand_trigger_filter(trigger, expand_fields)
    expand_trigger_action_filter(trigger, expand_fields)

    serializer_class = multiple_create_serializer_class(
        Trigger, expand_fields=expand_fields, exclude_fields=exclude_fields
    )
    serializer = serializer_class(trigger)
    config = serializer.data

    utils.format_trigger_config(config)

    trigger_cache.set_config(slug, json.dumps(config))
    return config


def expand_trigger_filter(trigger, expand_fields):
    max_layer = TriggerFilter.objects.filter(trigger__id=trigger.id).aggregate(max=Max('layer'))['max']
    for i in range(max_layer):
        if i == 0:
            expand_fields.append('triggerfilter_set.children')
        else:
            expand_fields.append(expand_fields[-1] + '.children')


def expand_trigger_action_filter(trigger, expand_fields):
    max_layer = TriggerActionFilter.objects.filter(action__trigger__id=trigger.id).aggregate(max=Max('layer'))['max']
    for i in range(max_layer):
        if i == 0:
            expand_fields.append('triggeraction_set.triggeractionfilter_set.children')
        else:
            expand_fields.append(expand_fields[-1] + '.children')


def list_trigger_config(app=None, model=None, event=None):
    if app:
        if model:
            if event:
                apis = Trigger.objects.filter(app=app, model=model, event=event).values('slug').all()
            else:
                apis = Trigger.objects.filter(app=app, model=model).values('slug').all()
        else:
            apis = Trigger.objects.filter(app=app).values('slug').all()
    else:
        apis = Trigger.objects.values('slug').all()
    results = []
    for api in apis:
        r = get_trigger_config(api['slug'])
        results.append(r)

    return results


def add_trigger(config):
    """新建触发器"""
    slug = config.get('slug', '')
    api = Trigger.objects.filter(slug=slug).first()
    if api:
        raise exceptions.BusinessException(error_code=exceptions.SLUG_EXISTS)

    save_trigger(config)


def update_trigger(id, config):
    """更新触发器"""
    save_trigger(config, id)


def save_trigger(config, id=None):
    """触发器配置信息保存到数据库"""
    with transaction.atomic():
        if id is None:
            slug = config.get('slug')
            trigger = Trigger.objects.filter(slug=slug).first()
            if not trigger:
                trigger = Trigger()
                trigger.slug = slug
                is_create = True
            else:
                is_create = False
        else:
            trigger = Trigger.objects.get(id=id)
            is_create = False

        trigger.app = config.get('app')
        trigger.model = config.get('model')
        try:
            model_class = apps.get_model(trigger.app, trigger.model)
        except LookupError:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'{trigger.app}__{trigger.model} 不是有效的model',
            )
        
        if 'name' in config:
            trigger.name = config['name']
        else:
            trigger.name = ''

        if 'summary' in config:
            trigger.summary = config['summary']
        else:
            trigger.summary = ''

        trigger.event = config['event']
        if trigger.event not in const.TRIGGER_EVENTS:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {trigger.event} 不是合法的触发器事件',
            )

        trigger.save()

        save_trigger_filter(trigger, config.get('triggerfilter'), is_create)
        save_trigger_action(trigger, config.get('triggeraction'), is_create)


def save_trigger_filter(trigger: Trigger, filters, is_create):
    if not is_create:
        TriggerFilter.objects.filter(trigger__id=trigger.id).delete()

    for f in filters:
        save_one_trigger_filter(trigger, f)


def save_one_trigger_filter(trigger: Trigger, f: TriggerFilter, parent=None):
    filter_model = TriggerFilter()
    filter_model.trigger = trigger
    if parent:
        filter_model.parent = parent
        filter_model.layer = parent.layer + 1
    else:
        filter_model.layer = 0
    if 'children' in f:
        filter_model.type = const.TRIGGER_FILTER_TYPE_CONTAINER
        filter_model.operator = f.get('operator')
        filter_model.save()

        children = f.get('children', [])
        for child in children:
            save_one_trigger_filter(trigger, child, filter_model)
    else:
        filter_model.type = const.TRIGGER_FILTER_TYPE_CHILD
        filter_model.field = f.get('field')
        filter_model.operator = f.get('operator')
        if 'value' in f:
            filter_model.value = json.dumps(f.get('value'))
        filter_model.save()


def save_trigger_action(trigger: Trigger, actions, is_create):
    if not is_create:
        TriggerAction.objects.filter(trigger__id=trigger.id).delete()

    for action in actions:
        action_model = TriggerAction()
        action_model.trigger = trigger
        action_model.action = action['action']
        if action_model.action not in const.TRIGGER_ACTIONS:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {trigger.event} 不是合法的触发器行为',
            )
        action_model.save()

        if 'triggeractionset' in action:
            save_trigger_action_set(action_model, action['triggeractionset'], is_create)

        if 'triggeractionfilter' in action:
            save_trigger_action_filters(action_model, action['triggeractionfilter'], is_create)


def save_trigger_action_set(action, sets, is_create):
    if not is_create:
        TriggerActionSet.objects.filter(action__id=action.id).delete()

    for s in sets:
        set_model = TriggerActionSet()
        set_model.action = action
        set_model.field = s['field']
        set_model.value = s['value']
        set_model.save()


def save_trigger_action_filters(action: TriggerAction, filters: list, is_create):
    if not is_create:
        TriggerActionFilter.objects.filter(action__id=action.id).delete()

    for f in filters:
        save_one_trigger_action_filter(action, f)


def save_one_trigger_action_filter(action: TriggerAction, f: TriggerActionFilter, parent=None):
    filter_model = TriggerActionFilter()
    filter_model.action = action
    if parent:
        filter_model.parent = parent
        filter_model.layer = parent.layer + 1
    else:
        filter_model.layer = 0

    if 'children' in f:
        filter_model.type = const.TRIGGER_ACTION_FILTER_TYPE_CONTAINER
        filter_model.operator = f.get('operator')
        filter_model.save()

        children = f.get('children')
        for child in children:
            save_one_trigger_action_filter(action, child, filter_model)
    else:
        filter_model.type = const.TRIGGER_ACTION_FILTER_TYPE_CHILD
        filter_model.field = f.get('field')
        filter_model.operator = f.get('operator')
        if 'value' in f:
            filter_model.value = json.dumps(f.get('value'))
        filter_model.save()


class DBDriver(utils.APIDriver):
    def add_api(self, config):
        add_api(config)

    def update_api(self, id, config):
        update_api(id, config)

    def save_api(self, config, id=None):
        save_api(config, id)

    def get_api_config(self, slug):
        return get_api_config(slug)

    def list_api_config(self, app=None):
        return list_api_config(app)

    def get_trigger_config(self, slug):
        return get_trigger_config(slug)

    def list_trigger_config(self, app=None, model=None, event=None):
        return list_trigger_config(app, model, event)

    def add_trigger(self, config):
        add_trigger(config)

    def update_trigger(self, id, config):
        update_trigger(id, config)

    def save_trigger(self, config, id=None):
        save_trigger(config, id)


driver = DBDriver()
