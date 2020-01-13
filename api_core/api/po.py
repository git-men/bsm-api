import json
from django.apps import apps

from . import const
from api_basebone.core import exceptions


class ApiPO:
    # def __init__(self):
    #     pass

    def __str__(self):
        return self.slug

    def __getitem__(self, k):
        return getattr(self, k)

    def __setitem__(self, k, v):
        return setattr(self, k, v)

    @property
    def method(self):
        '''API提交的方法'''
        return const.METHOD_MAP.get(self.operation)

    @property
    def expand_fields_set(self):
        '''展开字段的集合'''
        if self.expand_fields:
            return set(self.expand_fields.replace(' ', '').split(','))
        else:
            return set()

    def method_equal(self, method):
        return method.lower() in self.method

    def get_order_by_fields(self):
        if self.ordering:
            return self.ordering.replace(' ', '').split(',')
        else:
            return set()


class ParameterPO:
    # def __init__(self):
    #     pass

    def to_set_field_config(self):
        config = {'name': self.name, 'value': f'${{{self.name}}}'}
        if hasattr(self, 'children'):
            config['children'] = [
                p.to_set_field_config()
                for p in self.children
                if not p.is_special_defined()
            ]
        return config

    def is_special_defined(self):
        """自定义参数，用于特殊用途"""
        return self.type in const.SPECIAL_TYPES

    def __getitem__(self, k):
        return getattr(self, k)

    def __setitem__(self, k, v):
        return setattr(self, k, v)

    def __str__(self):
        return self.name


class DisplayFieldPO:
    # def __init__(self):
    #     pass

    def __str__(self):
        return self.name

    def __getitem__(self, k):
        return getattr(self, k)

    def __setitem__(self, k, v):
        return setattr(self, k, v)


class SetFieldPO:
    # def __init__(self):
    #     pass

    def __str__(self):
        return self.name

    def __getitem__(self, k):
        return getattr(self, k)

    def __setitem__(self, k, v):
        return setattr(self, k, v)

    def toDict(self):
        d = {}
        d['name'] = self.name
        d['value'] = self.value
        d['layer'] = self.layer
        if hasattr(self, 'children'):
            d['children'] = []
            for f in self.children:
                child = f.toDict()
                d['children'].append(child)
        return d


class FilterPO:
    # def __init__(self):
    #     pass

    def __getitem__(self, k):
        return getattr(self, k)

    def __setitem__(self, k, v):
        return setattr(self, k, v)

    def toDict(self):
        d = {}
        d['type'] = self.type
        # if hasattr(self, 'parent'):
        #     d['parent'] = self.parent
        if hasattr(self, 'field'):
            d['field'] = self.field
        d['operator'] = self.operator
        if hasattr(self, 'value'):
            d['value'] = self.value
        d['layer'] = self.layer
        if hasattr(self, 'children'):
            d['children'] = []
            for f in self.children:
                child = f.toDict()
                d['children'].append(child)
        return d

    def __str__(self):
        if self.type == const.FILTER_TYPE_CONTAINER:
            return f'{self.operator}'
        elif self.type == const.FILTER_TYPE_CHILD:
            return f'{self.field} {self.operator} {self.value}'
        else:
            return ''


def loadAPIFromConfig(config):
    api = ApiPO()
    slug = config.get('slug', '')
    api.slug = slug
    api.config = config
    api.app = config.get('app')
    api.model = config.get('model')

    api.logined = config.get('logined', True)
    api.disable = config.get('disable', False)

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

    api.name = config.get('name', '')
    api.summary = config.get('summary', '')
    api.demo = config.get('demo', '')

    if 'ordering' in config:
        if isinstance(config['ordering'], list):
            api.ordering = ",".join(config['ordering'])
        else:
            api.ordering = config['ordering']
    else:
        api.ordering = ''
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
                error_data=f'\'operation\': {api.operation} 操作，必须有func_name函数名',
            )

    api.parameter = loadParametersFromConfig(api, config.get('parameter'))
    api.displayfield = loadDisplayFieldFromConfig(api, config.get('displayfield'))
    api.setfield = loadSetFieldFromConfig(
        api, config.get('setfield'), model_class, api.parameter
    )
    api.filter = loadFilterFromConfig(api, config.get('filter'))

    permission = config.get('permission', {})
    api.groups = permission.get('group', [])

    return api


def loadParametersFromConfig(api, parameters, parent=None):
    if not parameters:
        return []

    pk_count = 0
    po_list = []
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

        po = ParameterPO()
        po.api = api
        po.name = param.get('name')
        if parent:
            po.parent = parent
            po.layer = parent.layer + 1
            po.fullname = parent.fullname + '.' + po.name
        else:
            po.layer = 0
            po.fullname = po.name
        po.desc = param.get('desc')
        po.type = param_type
        po.required = param.get('required')

        if 'is_array' in param:
            po.is_array = param.get('is_array')
        else:
            po.is_array = False

        if 'default' in param:
            po.default = param.get('default')
            po.use_default = True
        else:
            po.default = None
            po.use_default = False

        if 'children' in param:
            po.children = loadParametersFromConfig(api, param['children'], po)
        po_list.append(po)

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

    return po_list


def loadDisplayFieldFromConfig(api, fields):
    if not fields:
        return []

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

    po_list = []
    for field in fields:
        po = DisplayFieldPO()
        po.api = api
        if isinstance(field, str):
            po.name = field
        elif isinstance(field, dict):
            po.name = field.get('name')
        else:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data='display-fields的格式不对',
            )
        po_list.append(po)
    return po_list


def loadSetFieldFromConfig(api, fields, model_class, param_list):
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
            return []

    if not fields:
        fields = [
            p.to_set_field_config() for p in param_list if not p.is_special_defined()
        ]

    po_list = []
    meta_filed_names = [f.name for f in model_class._meta.get_fields()]
    for field in fields:
        po = loadOneSetField(api, field, meta_filed_names)
        po_list.append(po)

    return po_list


def loadOneSetField(api, field, meta_filed_names, parent=None):
    po = SetFieldPO()
    po.api = api
    children = None
    if isinstance(field, list) and len(field) == 2:
        po.name = field[0]
        po.value = field[1]
    elif isinstance(field, dict):
        po.name = field.get('name')
        po.value = field.get('value')
        if 'children' in field:
            children = field['children']
    else:
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR, error_data='set-fields的格式不对'
        )

    if parent:
        po.parent = parent
        po.fullname = parent.fullname + '.' + po.name
        po.layer = parent.layer + 1
    else:
        po.layer = 0
        po.fullname = po.name
        if po.name not in meta_filed_names:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'{api.app}__{api.model} 没有属性{po.name}',
            )

    if children:
        po.children = [loadOneSetField(api, f, meta_filed_names, po) for f in children]
    else:
        po.children = []

    return po


def loadFilterFromConfig(api, filters):
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
        return []

    if api.operation not in (
        const.OPERATION_LIST,
        const.OPERATION_UPDATE_BY_CONDITION,
        const.OPERATION_DELETE_BY_CONDITION,
    ):
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'\'operation\': {api.operation} 操作不需要filters条件',
        )

    po_list = []
    for filter in filters:
        po = loadOneFilter(api, filter)
        po_list.append(po)

    return po_list


def loadOneFilter(api, filter, parent=None):
    if 'children' in filter:
        po = FilterPO()
        po.api = api
        po.type = const.FILTER_TYPE_CONTAINER
        if parent:
            po.parent = parent
            po.layer = parent.layer + 1
        else:
            po.layer = 0
        po.operator = filter.get('operator')

        children = filter.get('children')
        po.children = []
        for child in children:
            child_po = loadOneFilter(api, child, po)
            po.children.append(child_po)
    else:
        po = FilterPO()
        po.api = api
        po.type = const.FILTER_TYPE_CHILD
        if parent:
            po.parent = parent
            po.layer = parent.layer + 1
        else:
            po.layer = 0
        po.field = filter.get('field')
        po.operator = filter.get('operator')
        if 'value' in filter:
            po.value = filter.get('value')

    return po


class TriggerPO:
    '''触发器'''
    slug = None
    app = None
    model = None
    name = None
    summary = None
    event = None
    triggerfilter = None
    triggeraction = None
    disable = None

    def is_create(self) -> bool:
        return self.event in (const.TRIGGER_EVENT_BEFORE_CREATE, const.TRIGGER_EVENT_AFTER_CREATE)

    def is_updae(self) -> bool:
        return self.event in (const.TRIGGER_EVENT_BEFORE_UPDATE, const.TRIGGER_EVENT_AFTER_UPDATE)

    def is_delete(self) -> bool:
        return self.event in (const.TRIGGER_EVENT_BEFORE_DELETE, const.TRIGGER_EVENT_AFTER_DELETE)

    def __str__(self):
        return '%s object (%s,%s,%s,%s)' % (
            self.__class__.__name__,
            self.slug,
            self.app,
            self.model,
            self.event,
        )

    class Meta:
        verbose_name = '触发器'
        verbose_name_plural = '触发器'


class TriggerFilterPO:
    '''触发器条件'''
    trigger: TriggerPO = None
    type = None
    parent = None
    field: str = None
    operator = None
    value: str = None
    layer = None
    children: list = None
    real_value = None

    def is_container(self):
        return self.type == const.TRIGGER_FILTER_TYPE_CONTAINER

    def is_filter_attribute(self):
        """value按照属性过滤"""
        value = self.get_real_value()
        if isinstance(value, str):
            return value.startswith('${')

    def is_filter_param(self):
        """value按照服务端变量过滤"""
        value = self.get_real_value()
        if isinstance(value, str):
            return value.startswith('#{')

    def get_real_value(self):
        if self.real_value is None:
            self.real_value = json.loads(self.value)
        return self.real_value

    def __str__(self):
        return '%s object (%s,%s,%s)' % (
            self.__class__.__name__,
            self.field,
            self.operator,
            self.value,
        )


class TriggerActionPO:
    '''触发器行为'''

    trigger = None
    action = None
    app = None
    model = None
    fields = None
    filters = None

    config = None


# class TriggerActionSetPO:
#     '''触发器写行为'''

#     action = None
#     field = None
#     value = None


# class TriggerActionFilterPO:
#     action = None
#     type = None
#     parent = None
#     field = None
#     operator = None
#     value = None
#     layer = None


def loadTrigger(config):
    trigger = TriggerPO()
    trigger.slug = config.get('slug')

    trigger.app = config.get('app')
    trigger.model = config.get('model')
    trigger.disable = config.get('disable', False)
    try:
        model_class = apps.get_model(trigger.app, trigger.model)
    except LookupError:
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'{trigger.app}__{trigger.model} 不是有效的model',
        )

    trigger.name = config.get('name', '')
    trigger.summary = config.get('summary', '')

    trigger.event = config['event']
    if trigger.event not in const.TRIGGER_EVENTS:
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'\'operation\': {trigger.event} 不是合法的触发器事件',
        )

    loadTriggerFilter(trigger, config.get('triggerfilter'))
    loadTriggerAction(trigger, config.get('triggeraction'))
    return trigger


def loadTriggerFilter(trigger: TriggerPO, filters: list):
    trigger.triggerfilter = [loadOneTriggerFilter(trigger, f) for f in filters]


def loadOneTriggerFilter(trigger: TriggerPO, f: TriggerFilterPO, parent=None):
    filter_po = TriggerFilterPO()
    filter_po.trigger = trigger
    if parent:
        filter_po.parent = parent
        filter_po.layer = parent.layer + 1
    else:
        filter_po.layer = 0
    if 'children' in f:
        filter_po.type = const.TRIGGER_FILTER_TYPE_CONTAINER
        filter_po.operator = f.get('operator')

        filter_po.children = [loadOneTriggerFilter(trigger, child, filter_po) for child in f.get('children', [])]
    else:
        filter_po.type = const.FILTER_TYPE_CHILD
        filter_po.field = f.get('field')
        filter_po.operator = f.get('operator')
        if 'value' in f:
            filter_po.value = json.dumps(f.get('value'))

    return filter_po


def loadTriggerAction(trigger: TriggerPO, actions: list):
    trigger.triggeraction = []
    for action in actions:
        action_po = TriggerActionPO()
        action_po.config = action
        action_po.trigger = trigger
        action_po.action = action['action']
        if action_po.action not in const.TRIGGER_ACTIONS:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {trigger.event} 不是合法的触发器行为',
            )
        trigger.triggeraction.append(action_po)

        # if 'triggeractionset' in action:
        #     loadTriggerActionSet(action_po, action['triggeractionset'])

        # if 'triggeractionfilter' in action:
        #     loadTriggerActionSetFilter(action_po, action['triggeractionfilter'])

        if 'fields' in action:
            action_po.fields = action['fields']

        if 'filters' in action:
            action_po.filters = action['filters']


# def loadTriggerActionSet(action: TriggerActionPO, sets: list):
#     action.triggeractionset = []
#     for s in sets:
#         po = TriggerActionSetPO()
#         po.action = action
#         po.field = s['field']
#         po.value = s['value']
#         action.triggeractionset.append(po)


# def loadTriggerActionSetFilter(action: TriggerActionPO, filters: list):
#     action.triggeractionfilter = [loadOneTriggerActionSetFilter(action, f) for f in filters]


# def loadOneTriggerActionSetFilter(action: TriggerActionPO, f: TriggerActionFilterPO, parent=None):
#     po = TriggerActionFilterPO()
#     po.action = action
#     if parent:
#         po.parent = parent
#         po.layer = parent.layer + 1
#     else:
#         po.layer = 0

#     if 'children' in f:
#         po.type = const.TRIGGER_ACTION_FILTER_TYPE_CONTAINER
#         po.operator = f.get('operator')

#         children = f.get('children')
#         po.children = [loadOneTriggerActionSetFilter(action, child, po) for child in children]
#     else:
#         po.type = const.TRIGGER_ACTION_FILTER_TYPE_CHILD
#         po.field = f.get('field')
#         po.operator = f.get('operator')
#         if 'value' in f:
#             po.value = json.dumps(f.get('value'))

#     return po
