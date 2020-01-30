from django.apps import apps

from . import const
from api_basebone.core import exceptions


class TriggerPO:
    '''触发器'''

    slug = None
    app = None
    model = None
    name = None
    summary = None
    event = None
    triggercondition = None
    triggeraction = None
    disable = None

    def is_create(self) -> bool:
        return self.event in (
            const.TRIGGER_EVENT_BEFORE_CREATE,
            const.TRIGGER_EVENT_AFTER_CREATE,
        )

    def is_updae(self) -> bool:
        return self.event in (
            const.TRIGGER_EVENT_BEFORE_UPDATE,
            const.TRIGGER_EVENT_AFTER_UPDATE,
        )

    def is_delete(self) -> bool:
        return self.event in (
            const.TRIGGER_EVENT_BEFORE_DELETE,
            const.TRIGGER_EVENT_AFTER_DELETE,
        )

    def __str__(self):
        return '%s object (%s,%s,%s,%s)' % (
            self.__class__.__name__,
            self.slug,
            self.app,
            self.model,
            self.event,
        )


class TriggerConditionPO:
    """触发器条件"""

    trigger = None
    app = None
    model = None
    filters = None

    def __str__(self):
        return '%s object (%s,%s)' % (self.__class__.__name__, self.app, self.model)


class TriggerActionPO:
    '''触发器行为'''

    trigger = None
    action = None
    app = None
    model = None
    fields = None
    filters = None

    config = None


def loadTrigger(config):
    trigger = TriggerPO()
    trigger.slug = config.get('slug')

    trigger.disable = config.get('disable', False)

    trigger.name = config.get('name', '')
    trigger.summary = config.get('summary', '')

    trigger.event = config['event']
    if trigger.event not in const.TRIGGER_EVENTS:
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'\'operation\': {trigger.event} 不是合法的触发器事件',
        )

    loadTriggerCondition(trigger, config.get('triggercondition'))
    loadTriggerAction(trigger, config.get('triggeraction'))
    return trigger


def loadTriggerCondition(trigger: TriggerPO, condition: dict):
    condition_po = TriggerConditionPO()
    for attr, value in condition.items():
        if hasattr(condition_po, attr):
            setattr(condition_po, attr, value)
    trigger.triggercondition = condition_po

    try:
        apps.get_model(condition_po.app, condition_po.model)
    except LookupError:
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'{condition_po.app}__{condition_po.model} 不是有效的model',
        )


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

        if 'fields' in action:
            action_po.fields = action['fields']

        if 'filters' in action:
            action_po.filters = action['filters']
