from django.apps import apps
from api_core.services.expresstion import resolve_expression


def convert_filters(filters_config, variables):
    result = {}
    for f in filters_config:
        # TODO
        result[f['field']] = resolve_expression(f['expression'], variables=variables)
    return result


def convert_fields(fields_config, variables):
    return {f: resolve_expression(exp, variables=variables) for f, exp in fields_config.items()}


ACTIONS = {}


def reg_action(func):
    ACTIONS[func.__name__] = func
    return func


@reg_action
def update(conf, variables):
    model = apps.get_model(conf['app'], conf['model'])
    filters = convert_filters(conf['filters'], variables=variables)
    fields = convert_fields(conf['fields'], variables=variables)
    model.objects.filter(**filters).update(**fields)


@reg_action
def create(conf, variables):
    model = apps.get_model(conf['app'], conf['model'])
    fields = convert_fields(conf['fields'], variables=variables)
    model.objects.create(**fields)


@reg_action
def delete(conf, variables):
    model = apps.get_model(conf['app'], conf['model'])
    filters = convert_filters(conf['filters'], variables=variables)
    model.objects.filter(**filters).delete()


@reg_action
def modify(conf, variables):
    for field, value in convert_fields(conf['fields'], variables=variables).items():
        setattr(variables.new, field, value)


class Variable:
    id = None
    old = None
    new = None
    user = None

    def __init__(self, id=None, old=None, new=None, user=None):
        self.id = id
        self.old = old
        self.new = new
        self.user = user


def run_action(conf, **kwargs):
    ACTIONS[conf.pop('action')](conf, Variable(**kwargs))
