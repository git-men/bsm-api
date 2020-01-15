import logging
import json
import re
import traceback

from api_basebone.core import exceptions

from ..api import api_param
from ..api import const
from ..api import po
from ..api import utils

from .trigger_actions import run_action

log = logging.getLogger('django')


def add_trigger(config):
    driver = utils.get_api_driver()
    return driver.add_trigger(config)


def update_trigger(id, config):
    driver = utils.get_api_driver()
    return driver.update_trigger(id, config)


def save_trigger(config, id=None):
    driver = utils.get_api_driver()
    return driver.save_trigger(config, id)


def get_trigger_config(slug):
    driver = utils.get_api_driver()
    config = driver.get_trigger_config(slug)
    return config


def list_trigger(event=None, *args, **kwargs):
    # print(f'list_trigger:{event},{kwargs}')
    driver = utils.get_api_driver()
    return driver.list_trigger_config(event, *args, **kwargs)


def exists_trigger(event=None, disable=False, *args, **kwargs) -> bool:
    """
    """
    triggers = list_trigger(event, *args, **kwargs)
    triggers = [t for t in triggers if t.get('disable', False) is disable]
    return len(triggers) > 0


def get_trigger_po(slug, config=None) -> po.TriggerPO:
    if not config:
        config = get_trigger_config(slug)

    if not config:
        raise exceptions.BusinessException(
            error_code=exceptions.INVALID_API, error_data=f'缺少trigger：{slug}'
        )
    trigger = po.loadTrigger(config)
    return trigger


def list_trigger_po(event=None, *args, **kwargs) -> list:
    trigger_list = list_trigger(event, *args, **kwargs)
    po_list = []
    for config in trigger_list:
        slug = ''
        try:
            slug = config['slug']
            trigger = get_trigger_po(config['slug'], config)
            po_list.append(trigger)
        except Exception as e:
            print(f'触发器 {slug} 异常:' + str(e) + "," + traceback.format_exc())
    return po_list


def handle_triggers(
    request, event, id=None, old_inst=None, new_inst=None, *args, **kwargs
):
    slug = ''
    try:
        trigger_list = list_trigger_po(event, *args, **kwargs)
        for trigger in trigger_list:
            if trigger.disable:
                """此触发器已经停用"""
                continue
            slug = trigger.slug
            if check_trigger(request, trigger, old_inst, new_inst):
                run_trigger(request, trigger, id, old_inst, new_inst)
    except exceptions.BusinessException as e:
        print(
            f'事件 {event}.{slug}:{kwargs} 的触发器有异常:' + str(e) + "," + traceback.format_exc()
        )
        raise e
    except Exception as e:
        print(
            f'事件 {event}.{slug}:{kwargs} 的触发器有异常:' + str(e) + "," + traceback.format_exc()
        )
        raise exceptions.BusinessException(
            error_code=exceptions.TRIGGER_ERROR,
            error_data=f'事件 {event}.{slug}:{kwargs} 的触发器有异常',
        )


def is_container_config(filter_config: dict):
    return 'children' in filter_config


def is_filter_attribute(value):
    """value按照属性过滤"""
    if isinstance(value, str):
        return value.startswith('${')
    else:
        return False


def is_filter_param(value):
    """value按照服务端变量过滤"""
    if isinstance(value, str):
        return value.startswith('#{')
    else:
        return False


def check_trigger(request, trigger_po: po.TriggerPO, old_inst, new_inst) -> bool:
    condition = trigger_po.triggercondition
    # print(f'check_trigger:{condition},{condition.filters}')
    result = check_filters(request, trigger_po, condition.filters, old_inst, new_inst)
    return result


def check_filters(
    request, trigger_po: po.TriggerPO, filters: list, old_inst, new_inst, conn='and'
) -> bool:
    """
    conn:Connection types 条件关联逻辑，AND和OR 两种，第一层默认为and
    """
    # print(f'check_filters:{filters}')
    conn = conn.lower()
    if conn == 'and':
        is_and = True
    elif conn == 'or':
        is_and = False
    else:
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'条件关联逻辑只有 and 和 or, 没有 {conn}',
        )

    for f in filters:
        f: dict
        if is_container_config(f):
            result = check_filters(
                request, trigger_po, f['children'], old_inst, new_inst, f['operator']
            )
        else:
            result = check_one_filter(request, trigger_po, f, old_inst, new_inst)

        # print(f'check_filters:{f}, {result}')

        if is_and and (not result):
            """与逻辑，遇假得假"""
            return False

        if (not is_and) and result:
            """或逻辑，遇真得真"""
            return True

    if is_and:
        """与逻辑，全真得真"""
        return True
    else:
        """或逻辑，全假得假"""
        return False


def check_one_filter(
    request, trigger_po: po.TriggerPO, f: dict, old_inst, new_inst
) -> bool:
    left = getFilterLeftValue(request, trigger_po, f, old_inst, new_inst)
    right = getFilterRightValue(request, trigger_po, f, old_inst, new_inst)

    if f['operator'] in const.COMPARE_OPERATOR:
        op = const.COMPARE_OPERATOR[f['operator']]
        result = op(left, right)
        # print(f'check_one_filter:{f}, {left}, {f.operator}, {right}, {result}')
        return result
    else:
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'触发器不支持比较符号"{f.operator}"',
        )


def getFilterLeftValue(request, trigger_po: po.TriggerPO, f: dict, old_inst, new_inst):
    return getFilterValue(request, trigger_po, f['field'], old_inst, new_inst)


def getFilterRightValue(request, trigger_po: po.TriggerPO, f: dict, old_inst, new_inst):
    return getFilterValue(request, trigger_po, f.get('expression'), old_inst, new_inst)


def getFilterValue(request, trigger_po: po.TriggerPO, value, old_inst, new_inst):
    if is_filter_attribute(value):
        pat = r'\${([\w\.-]+)}'
        fields = re.findall(pat, value)
        return getFilterValueFromInst(trigger_po, fields[0], old_inst, new_inst)
    elif is_filter_param(value):
        pat = r'#{([\w\.-]+)}'
        params = re.findall(pat, value)
        if params[0] not in api_param.API_SERVER_PARAM:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'服务端参数\'{params[0]}\'为未定义参数',
            )
        f = api_param.API_SERVER_PARAM[params[0]]
        return f(request)
    else:
        return value


def getFilterValueFromInst(trigger_po: po.TriggerPO, field: str, old_inst, new_inst):
    attr = field.split('.')
    if attr[0] == const.OLD_INSTANCE:
        if trigger_po.is_create():
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'新建操作的触发器不支持old_inst',
            )

        inst = old_inst
    elif attr[0] == const.NEW_INSTANCE:
        if trigger_po.is_delete():
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data=f'删除操作的触发器不支持new_inst',
            )

        inst = new_inst
    else:
        raise exceptions.BusinessException(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'触发器不支持对象"{attr[0]}"',
        )
    return getattr(inst, attr[1])


def run_trigger(request, trigger_po: po.TriggerActionPO, id, old_inst, new_inst):
    # print(f'run_trigger:{id}')
    for action in trigger_po.triggeraction:
        run_action(action.config, id=id, old=old_inst, new=new_inst, user=request.user)

