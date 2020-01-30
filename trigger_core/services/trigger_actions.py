from django.apps import apps
from api_basebone.services.expresstion import resolve_expression
from api_basebone.utils import queryset as queryset_util


def convert_fields(fields_config, variables):
    return {f: resolve_expression(exp, variables=variables) for f, exp in fields_config.items()}


ACTIONS = {}


def reg_action(func):
    ACTIONS[func.__name__] = func
    return func


@reg_action
def update(conf, variables):
    model = apps.get_model(conf['app'], conf['model'])
    fields = convert_fields(conf['fields'], variables=variables)
    queryset_util.filter(model.objects, conf['filters'], context=variables).update(**fields)


@reg_action
def create(conf, variables):
    model = apps.get_model(conf['app'], conf['model'])
    fields = convert_fields(conf['fields'], variables=variables)
    model.objects.create(**fields)


@reg_action
def delete(conf, variables):
    model = apps.get_model(conf['app'], conf['model'])
    queryset_util.filter(model.objects, conf['filters'], context=variables).delete()


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
