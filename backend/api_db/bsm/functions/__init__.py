from api_basebone.restful.funcs import bsm_func, functions_for_model

from ...models import Api, Function

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


@bsm_func(staff_required=True, name='cloud_functions', model=Function)
def cloud_functions(user, model, scene=Function.SCENE_UNLIMIT, **kwargs):
    """返回所有云函数，包括代码定义和数据表中定义的云函数。
    """
    functions = []
    db_funcs = Function.objects.filter(model=model, enable=True, scene=scene).prefetch_related('functionparameter_set')
    for func in db_funcs:
        functions.append({
            'name': func.name,
            'model': func.model,
            'description': func.description,
            'scene': func.scene,
            'login_required': func.login_required,
            'staff_required': func.staff_required,
            'superuser_required': func.superuser_required,
            'params': [
                {
                    'name': param.name,
                    'displayName': param.display_name,
                    'type': param.type,
                    'ref': param.ref,
                    'required': param.required,
                    'description': param.description,
                    'nestedForm': False
                }
                for param in func.functionparameter_set.all()
            ]
        })
    code_funcs = functions_for_model(*model.split('__'))

    for name, value in code_funcs.items():
        func, options = value
        functions.append({
            'name': name,
            'model': func.model,
            'description': '',
            'scene': options.get('scene', Function.SCENE_UNLIMIT),
            'login_required': options['login_required'],
            'staff_required': options['staff_required'],
            'superuser_required': options['superuser_required'],
            'params': []
        })
    return functions
