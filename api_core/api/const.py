import operator

"""api相关常量"""

OPERATION_LIST = 'list'
OPERATION_RETRIEVE = 'retrieve'
OPERATION_CREATE = 'create'
OPERATION_UPDATE = 'update'
OPERATION_REPLACE = 'replace'
OPERATION_DELETE = 'delete'
OPERATION_UPDATE_BY_CONDITION = 'update_by_condition'
OPERATION_DELETE_BY_CONDITION = 'delete_by_condition'
OPERATION_FUNC = 'func'

OPERATIONS_CHOICES = (
    (OPERATION_LIST, '列表'),
    (OPERATION_RETRIEVE, '详情'),
    (OPERATION_CREATE, '新建'),
    (OPERATION_UPDATE, '全部更新'),
    (OPERATION_REPLACE, '部分更新'),
    (OPERATION_DELETE, '删除'),
    (OPERATION_UPDATE_BY_CONDITION, '批量更新'),
    (OPERATION_DELETE_BY_CONDITION, '批量删除'),
    (OPERATION_FUNC, '云函数'),
)

OPERATIONS = set([t[0] for t in OPERATIONS_CHOICES])

MATHOD_GET = 'get'
MATHOD_POST = 'post'
MATHOD_PUT = 'put'
MATHOD_DELETE = 'delete'
MATHOD_PATCH = 'patch'

METHOD_MAP = {
    OPERATION_LIST: (MATHOD_GET,),
    OPERATION_RETRIEVE: (MATHOD_GET,),
    OPERATION_CREATE: (MATHOD_POST,),
    OPERATION_UPDATE: (MATHOD_PUT,),
    OPERATION_REPLACE: (MATHOD_PATCH, MATHOD_PUT),
    OPERATION_DELETE: (MATHOD_DELETE,),
    OPERATION_UPDATE_BY_CONDITION: (MATHOD_PATCH, MATHOD_PUT),
    OPERATION_DELETE_BY_CONDITION: (MATHOD_DELETE,),
    OPERATION_FUNC: (MATHOD_POST,),
}

TYPE_STRING = 'string'
TYPE_INT = 'int'
TYPE_DECIMAL = 'decimal'
TYPE_BOOLEAN = 'boolean'
TYPE_JSON = 'json'
TYPE_OBJECT = 'object'
TYPE_PAGE_SIZE = 'PAGE_SIZE'
TYPE_PAGE_IDX = 'PAGE_IDX'
TYPE_PK = 'pk'
TYPES_CHOICES = (
    (TYPE_STRING, '字符串'),
    (TYPE_INT, '整数'),
    (TYPE_DECIMAL, '浮点数'),
    (TYPE_BOOLEAN, '布尔值'),
    (TYPE_JSON, 'json格式'),
    (TYPE_OBJECT, '复杂类型'),
    (TYPE_PAGE_SIZE, '页长'),
    (TYPE_PAGE_IDX, '页码'),
    (TYPE_PK, '主键'),
)
TYPES = set([t[0] for t in TYPES_CHOICES])

SPECIAL_TYPES = (TYPE_PAGE_SIZE, TYPE_PAGE_IDX, TYPE_PK)

FILTER_TYPE_CONTAINER = 0  # 容器
FILTER_TYPE_CHILD = 1  # 单一条件

DRIVER_DB = 'db'
DRIVER_JS = 'js'
DEFALUT_DRIVER = DRIVER_DB


TRIGGER_EVENT_BEFORE_CREATE = 'before_create'
TRIGGER_EVENT_AFTER_CREATE = 'after_create'
TRIGGER_EVENT_BEFORE_UPDATE = 'before_update'
TRIGGER_EVENT_AFTER_UPDATE = 'after_update'
TRIGGER_EVENT_BEFORE_DELETE = 'before_delete'
TRIGGER_EVENT_AFTER_DELETE = 'after_delete'
TRIGGER_EVENT_CHOICES = (
    (TRIGGER_EVENT_BEFORE_CREATE, '创建前'),
    (TRIGGER_EVENT_AFTER_CREATE, '创建后'),
    (TRIGGER_EVENT_BEFORE_UPDATE, '更新前'),
    (TRIGGER_EVENT_AFTER_UPDATE, '更新后'),
    (TRIGGER_EVENT_BEFORE_DELETE, '删除前'),
    (TRIGGER_EVENT_AFTER_DELETE, '删除后'),
)
TRIGGER_EVENTS = set([t[0] for t in TRIGGER_EVENT_CHOICES])

TRIGGER_FILTER_TYPE_CONTAINER = 0  # 容器
TRIGGER_FILTER_TYPE_CHILD = 1  # 单一条件
TRIGGER_FILTER_CHOICES = (
    (TRIGGER_FILTER_TYPE_CONTAINER, '容器'),
    (TRIGGER_FILTER_TYPE_CHILD, '单一条件'),
)
TRIGGER_FILTERS = set([t[0] for t in TRIGGER_FILTER_CHOICES])


TRIGGER_ACTION_REJECT = 'reject'
TRIGGER_ACTION_CREATE = 'create'
TRIGGER_ACTION_UPDATE = 'update'
TRIGGER_ACTION_DELETE = 'delete'
TRIGGER_ACTION_CHOICES = (
    (TRIGGER_ACTION_REJECT, '拒绝存储'),
    (TRIGGER_ACTION_CREATE, '创建记录'),
    (TRIGGER_ACTION_UPDATE, '更新记录'),
    (TRIGGER_ACTION_DELETE, '删除记录'),
)
TRIGGER_ACTIONS = set([t[0] for t in TRIGGER_ACTION_CHOICES])

TRIGGER_ACTION_FILTER_TYPE_CONTAINER = 0  # 容器
TRIGGER_ACTION_FILTER_TYPE_CHILD = 1  # 单一条件
TRIGGER_ACTION_FILTER_CHOICES = (
    (TRIGGER_ACTION_FILTER_TYPE_CONTAINER, '容器'),
    (TRIGGER_ACTION_FILTER_TYPE_CHILD, '单一条件'),
)
TRIGGER_ACTION_FILTERS = set([t[0] for t in TRIGGER_ACTION_FILTER_CHOICES])

OLD_INSTANCE = 'old'  # 修改前的model对象
NEW_INSTANCE = 'new'  # 修改后的model对象

# 比较符
COMPARE_OPERATOR = {
    '=': operator.eq,
    '==': operator.eq,
    '===': operator.eq,
    '!=': operator.ne,
    '<>': operator.ne,
    '>': operator.gt,
    '>=': operator.ge,
    '<': operator.lt,
    '<=': operator.le,
    'contains': operator.contains,
    'in': lambda a, b: a in b,
    'startswith': lambda a, b: a.startswith(b),
    'endswith': lambda a, b: a.endswith(b),
}
