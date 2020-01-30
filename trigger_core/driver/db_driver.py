import json
from django.db import transaction
from django.apps import apps

from api_basebone.core import exceptions
from api_basebone.restful.serializers import multiple_create_serializer_class
from ..cache import trigger_cache
from .. import const
from . import TriggerDriver

from .. import models
from ..models import Trigger
from ..models import TriggerCondition
from ..models import TriggerAction


def queryset_to_json(queryset, expand_fields, exclude_fields):
    serializer_class = multiple_create_serializer_class(
        queryset.model, expand_fields=expand_fields, exclude_fields=exclude_fields
    )
    serializer = serializer_class(queryset, many=True)
    return serializer.data


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
    expand_fields = ['triggercondition', 'triggeraction_set']
    exclude_fields = {
        'trigger_core__triggercondition': ['id', 'trigger', 'layer'],
        'trigger_core__triggeraction': ['id', 'trigger'],
    }

    serializer_class = multiple_create_serializer_class(
        Trigger, expand_fields=expand_fields, exclude_fields=exclude_fields
    )
    serializer = serializer_class(trigger)
    config = serializer.data

    trigger_cache.set_config(slug, json.dumps(config))
    return config


def add_trigger(config):
    """新建触发器"""
    slug = config.get('slug')
    if not slug:
        slug = models.UUID()
        config['slug'] = slug
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
            if not slug:
                slug = models.UUID()
                config['slug'] = slug
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

        if 'name' in config:
            """如果没有就用默认值"""
            trigger.name = config['name']

        if 'summary' in config:
            """如果没有就用默认值"""
            trigger.summary = config['summary']

        if 'disable' in config:
            """如果没有就用默认值"""
            trigger.disable = config['disable']

        trigger.event = config['event']
        if trigger.event not in const.TRIGGER_EVENTS:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {trigger.event} 不是合法的触发器事件',
            )

        trigger.save()

        save_trigger_condition(trigger, config.get('triggercondition'), is_create)
        save_trigger_action(trigger, config.get('triggeraction'), is_create)

        trigger_cache.delete_config(trigger.slug)


def save_trigger_condition(trigger: Trigger, condition: dict, is_create):
    if hasattr(trigger, 'triggercondition'):
        condition_model = trigger.triggercondition
    else:
        condition_model = TriggerCondition()
        condition_model.trigger = trigger

    for attr, value in condition.items():
        if hasattr(condition_model, attr):
            setattr(condition_model, attr, value)
    condition_model.save()

    try:
        apps.get_model(condition_model.app, condition_model.model)
    except LookupError:
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'{condition_model.app}__{condition_model.model} 不是有效的model',
        )


def save_trigger_action(trigger: Trigger, actions, is_create):
    if not is_create:
        TriggerAction.objects.filter(trigger__id=trigger.id).delete()

    for action in actions:
        action_model = TriggerAction()
        action_model.trigger = trigger
        action_model.action = action['action']
        action_model.app = action['app']
        action_model.model = action['model']
        if action_model.action not in const.TRIGGER_ACTIONS:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'\'operation\': {trigger.event} 不是合法的触发器行为',
            )

        if 'fields' in action:
            action_model.fields = action['fields']

        if 'filters' in action:
            action_model.filters = action['filters']

        action_model.save()


class DBDriver(TriggerDriver):
    def get_trigger_config(self, slug):
        return get_trigger_config(slug)

    def list_trigger_config(self, event=None, *args, **kwargs):
        kw = {f'triggercondition__{k}': v for k, v in kwargs.items()}
        print(f'list_trigger_config:{kw}')
        if event:
            apis = Trigger.objects.filter(event=event, **kw).values('slug').all()
        else:
            apis = Trigger.objects.filter(**kw).values('slug').all()
        results = []
        for api in apis:
            r = get_trigger_config(api['slug'])
            results.append(r)

        return results

    def add_trigger(self, config):
        add_trigger(config)

    def update_trigger(self, id, config):
        update_trigger(id, config)

    def save_trigger(self, config, id=None):
        save_trigger(config, id)


driver = DBDriver()
