import re
import json
from decimal import Decimal
from functools import reduce
from django.utils import timezone


def operator_wrap(func):
    return lambda *args: reduce(func, args)


def cmp_wrap(func):
    return lambda *args: bool(reduce(lambda a, b: a is not False and func(a, b) and b, args))


FUNCS = {
    'round': round,
    'getattr': getattr,
    'now': timezone.now,
    'today': lambda: timezone.now().date(),
    'max': max,
    'min': min,
    'add': operator_wrap(lambda a, b: a + b),
    'sub': operator_wrap(lambda a, b: a - b),
    'mul': operator_wrap(lambda a, b: a * b),
    'div': operator_wrap(lambda a, b: a / b),
    'mod': operator_wrap(lambda a, b: a % b),
    'pow': operator_wrap(lambda a, b: a ** b),
    'and': operator_wrap(lambda a, b: a and b),
    'or': operator_wrap(lambda a, b: a or b),
    'len': len,
    'decimal': Decimal,
    'lt': cmp_wrap(lambda a, b: a < b),
    'lte': cmp_wrap(lambda a, b: a <= b),
    'gt': cmp_wrap(lambda a, b: a > b),
    'gte': cmp_wrap(lambda a, b: a >= b),
    'eq': cmp_wrap(lambda a, b: a == b),
    'not': lambda x: not x,
    'getitem': lambda obj, key: obj[key],
    'in': lambda key, obj: key in obj,
    'if': lambda cond, a, b: a if cond else b,
    'slice': lambda obj, *args: obj[slice(*args)]
}


def split_expression(expression, symbol):
    quote = False
    surround = 0
    buffer = ''
    escape = False
    for char in expression:
        if escape and quote:
            escape = False
        else:
            if char == symbol:
                if surround == 0 and not quote:
                    yield buffer
                    buffer = ''
                    continue
            elif char == '\\':
                if quote:
                    escape = True
            elif char == '"':
                quote = not quote
            elif char in '([{':
                surround += 1
            elif char in ')]}':
                surround -= 1
        buffer += char
    if buffer:
        yield buffer


def resolve_expression(expression, variables):
    expression = expression.strip()

    try:
        return json.loads(expression)
    except json.JSONDecodeError:
        pass

    matched = re.match('^(\w+)\((.*)\)$', expression)
    if matched:
        func, arg_str = matched.groups()
        if func == 'variables':
            return variables
        args = [resolve_expression(buffer, variables=variables) for buffer in split_expression(arg_str, ',')]
        return FUNCS[func](*args)

    # 点操作符，getattr的语法糖
    exp = 'variables()'
    for path_item in expression.split('.'):
        exp = f'getattr({exp}, "{path_item}")'
    return resolve_expression(exp, variables=variables)
