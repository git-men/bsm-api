from api_basebone.restful.funcs import bsm_func

from ...models import Api

from api_core.services import api_services


@bsm_func(login_required=False, staff_required=True, name='show_api', model=Api)
def show_api(user, slug, **kwargs):
    return api_services.get_api_config(slug)


@bsm_func(login_required=False, staff_required=True, name='list_api', model=Api)
def list_api(user, app=None, **kwargs):
    return api_services.list_api(app)


@bsm_func(staff_required=True, name='add_api', model=Api)
def add_api(user, config, **kwargs):
    api_services.add_api(config)
    return api_services.get_api_config(config.get('slug', ''))


@bsm_func(staff_required=True, name='update_api', model=Api)
def update_api(user, id, config, **kwargs):
    api_services.update_api(id, config)
    return api_services.get_api_config(config.get('slug', ''))


@bsm_func(staff_required=True, name='api_save', model=Api)
def api_save(user, config, **kwargs):
    api_services.save_api(config)
    return api_services.get_api_config(config.get('slug', ''))
