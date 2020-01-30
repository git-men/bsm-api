import operator

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

DB_TRIGGER = (
    TRIGGER_EVENT_BEFORE_CREATE,
    TRIGGER_EVENT_AFTER_CREATE,
    TRIGGER_EVENT_BEFORE_UPDATE,
    TRIGGER_EVENT_AFTER_UPDATE,
    TRIGGER_EVENT_BEFORE_DELETE,
    TRIGGER_EVENT_AFTER_DELETE,
)

TRIGGER_FILTER_TYPE_CONTAINER = 0  # 容器
TRIGGER_FILTER_TYPE_CHILD = 1  # 单一条件
TRIGGER_FILTER_CHOICES = (
    (TRIGGER_FILTER_TYPE_CONTAINER, '容器'),
    (TRIGGER_FILTER_TYPE_CHILD, '单一条件'),
)
TRIGGER_FILTERS = set([t[0] for t in TRIGGER_FILTER_CHOICES])


# TRIGGER_ACTION_REJECT = 'reject'
# TRIGGER_ACTION_MODIFY = 'modify'
TRIGGER_ACTION_CREATE = 'create'
TRIGGER_ACTION_UPDATE = 'update'
TRIGGER_ACTION_DELETE = 'delete'
TRIGGER_ACTION_CHOICES = (
    # (TRIGGER_ACTION_REJECT, '终止执行'),
    # (TRIGGER_ACTION_MODIFY, '修改参数'),
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
