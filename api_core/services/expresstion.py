import re
import json
from decimal import Decimal
from functools import reduce
from django.utils import timezone

FUNCS = {
    'round': round,
    'getattr': getattr,
    'now': timezone.now,
    'max': max,
    'min': min,
    'add': lambda *args: reduce(lambda a, b: a+b, args),
    'and': lambda *args: all(args),
    'or': lambda *args: any(args),
    'len': len,
    'Decimal': Decimal,
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
