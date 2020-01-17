from . import const


handler_cache = {}


class TriggerHandler:
    def list_trigger(self, event, *args, **kwargs):
        pass

    def exists_trigger(self, event, *args, **kwargs):
        pass


class DBTriggerHandler:
    def list_trigger(self, event, app=None, model=None, *args, **kwargs):
        pass

    def exists_trigger(self, event, app=None, model=None, *args, **kwargs):
        pass


def GetTriggerHandler(event):
    if event in (
        const.TRIGGER_EVENT_BEFORE_CREATE,
        const.TRIGGER_EVENT_AFTER_CREATE,
        const.TRIGGER_EVENT_BEFORE_UPDATE,
        const.TRIGGER_EVENT_AFTER_UPDATE,
        const.TRIGGER_EVENT_BEFORE_DELETE,
        const.TRIGGER_EVENT_AFTER_DELETE,
    ):
        handler_type = DBTriggerHandler
    else:
        return None

    if handler_type not in handler_cache:
        handler_cache[handler_type] = handler_type()
    return handler_cache[handler_type]
