from django.dispatch import receiver

from api_core.api.views import ApiViewSet

from . import const
from .services import trigger_services

from api_core.signals import bsm_before_create
from api_core.signals import bsm_after_create
from api_core.signals import bsm_before_update
from api_core.signals import bsm_after_update
from api_core.signals import bsm_before_delete
from api_core.signals import bsm_after_delete


@receiver(bsm_before_create, sender=ApiViewSet, dispatch_uid='before_create')
def handle_before_create(sender, apiViewSet, new_inst, **kwargs):
    api = apiViewSet.api
    trigger_services.handle_triggers(
        apiViewSet.request,
        const.TRIGGER_EVENT_BEFORE_CREATE,
        id=new_inst.id,
        old_inst=None,
        new_inst=new_inst,
        app=api.app,
        model=api.model,
    )


@receiver(bsm_after_create, sender=ApiViewSet, dispatch_uid='after_create')
def handle_after_create(sender, apiViewSet, new_inst, **kwargs):
    api = apiViewSet.api
    trigger_services.handle_triggers(
        apiViewSet.request,
        const.TRIGGER_EVENT_AFTER_CREATE,
        id=new_inst.id,
        old_inst=None,
        new_inst=new_inst,
        app=api.app,
        model=api.model,
    )


@receiver(bsm_before_update, sender=ApiViewSet, dispatch_uid='before_update')
def handle_before_update(sender, apiViewSet, old_inst, new_inst, **kwargs):
    api = apiViewSet.api
    trigger_services.handle_triggers(
        apiViewSet.request,
        const.TRIGGER_EVENT_BEFORE_UPDATE,
        id=new_inst.id,
        old_inst=old_inst,
        new_inst=new_inst,
        app=api.app,
        model=api.model,
    )


@receiver(bsm_after_update, sender=ApiViewSet, dispatch_uid='after_update')
def handle_after_update(sender, apiViewSet, old_inst, new_inst, **kwargs):
    api = apiViewSet.api
    trigger_services.handle_triggers(
        apiViewSet.request,
        const.TRIGGER_EVENT_AFTER_UPDATE,
        id=new_inst.id,
        old_inst=old_inst,
        new_inst=new_inst,
        app=api.app,
        model=api.model,
    )


@receiver(bsm_before_delete, sender=ApiViewSet, dispatch_uid='before_delete')
def handle_before_delete(sender, apiViewSet, old_inst, **kwargs):
    api = apiViewSet.api
    trigger_services.handle_triggers(
        apiViewSet.request,
        const.TRIGGER_EVENT_BEFORE_DELETE,
        id=old_inst.id,
        old_inst=old_inst,
        new_inst=None,
        app=api.app,
        model=api.model,
    )


@receiver(bsm_after_delete, sender=ApiViewSet, dispatch_uid='after_delete')
def handle_after_delete(sender, apiViewSet, old_inst, **kwargs):
    api = apiViewSet.api
    trigger_services.handle_triggers(
        apiViewSet.request,
        const.TRIGGER_EVENT_AFTER_DELETE,
        id=old_inst.id,
        old_inst=old_inst,
        new_inst=None,
        app=api.app,
        model=api.model,
    )
