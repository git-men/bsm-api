from api_basebone.restful.funcs import bsm_func

from ...models import Trigger

from ...services import trigger_services


@bsm_func(login_required=False, staff_required=True, name='show_trigger', model=Trigger)
def show_trigger(user, slug, **kwargs):
    return trigger_services.get_trigger_config(slug)


@bsm_func(login_required=False, staff_required=True, name='list_trigger', model=Trigger)
def list_trigger(user, app=None, model=None, event=None, **kwargs):
    return trigger_services.list_trigger(app, model, event)


@bsm_func(staff_required=True, name='add_trigger', model=Trigger)
def add_trigger(user, config, **kwargs):
    trigger_services.add_trigger(config)
    return trigger_services.get_trigger_config(config.get('slug', ''))


@bsm_func(staff_required=True, name='update_trigger', model=Trigger)
def update_api(user, id, config, **kwargs):
    trigger_services.update_trigger(id, config)
    trigger = Trigger.objects.get(id=id)
    return trigger_services.get_trigger_config(trigger.slug)


@bsm_func(staff_required=True, name='save_trigger', model=Trigger)
def save_trigger(user, config, **kwargs):
    trigger_services.save_trigger(config)
    return trigger_services.get_trigger_config(config.get('slug', ''))
