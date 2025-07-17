#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2016-2024 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl

"""
Python equivalents of Excel operators.
"""
import schedula as sh
import functools
import collections
from . import (
    replace_empty, not_implemented, wrap_func, wrap_ufunc, Error, value_return
)
from .text import _str
from .look import _get_type_id

OPERATORS = collections.defaultdict(lambda: not_implemented)

numeric_wrap = functools.partial(wrap_ufunc, return_func=value_return)

def fuzzy_add(x, y):
    """
    Adds two values with better handling of floating-point errors.

    Tries to convert inputs to floats, adds them, and rounds to 6 decimals
    to avoid tiny precision issues. If conversion fails, falls back to normal addition.

    Args:
        x: First value (number or other).
        y: Second value (number or other).

    Returns:
        Rounded sum if numeric, else default addition result.
    """
    try:
        if isinstance(x, int) and isinstance(y, int):
            # Just add integers normally, no rounding needed
            return x + y
        else:
            # Convert to float and round to avoid floating-point issues
            sum_val = float(x) + float(y)
            return round(sum_val, 6)
    except (ValueError, TypeError):
        # fallback to normal addition or string concat etc.
        return x + y

# noinspection PyTypeChecker
OPERATORS.update({k: numeric_wrap(v) for k, v in {
    '+': fuzzy_add,
    '-': lambda x, y: x - y,
    'U-': lambda x: -x,
    '*': lambda x, y: x * y,
    '/': lambda x, y: (x / y) if y else Error.errors['#DIV/0!'],
    '^': lambda x, y: x ** y,
    '%': lambda x: x / 100.0,
}.items()})
OPERATORS['U+'] = wrap_ufunc(
    lambda x: x, input_parser=lambda *a: a, return_func=value_return
)


def logic_input_parser(x, y):
    if x is sh.EMPTY:
        x = '' if isinstance(y, str) else 0
    if y is sh.EMPTY:
        y = '' if isinstance(x, str) else 0
    return (_get_type_id(x), x), (_get_type_id(y), y)


logic_wrap = functools.partial(
    wrap_ufunc, input_parser=logic_input_parser, return_func=value_return,
    args_parser=lambda *a: a
)
LOGIC_OPERATORS = collections.OrderedDict([
    ('>=', lambda x, y: x >= y),
    ('<=', lambda x, y: x <= y),
    ('<>', lambda x, y: x != y),
    ('<', lambda x, y: x < y),
    ('>', lambda x, y: x > y),
    ('=', lambda x, y: x == y),
])
OPERATORS.update({k: logic_wrap(v) for k, v in LOGIC_OPERATORS.items()})
OPERATORS['&'] = wrap_ufunc(
    lambda x, y: x + y, input_parser=lambda *a: map(_str, a),
    args_parser=lambda *a: (replace_empty(v, '') for v in a),
    return_func=value_return
)
OPERATORS.update({k: wrap_func(v, ranges=True) for k, v in {
    ',': lambda x, y: x | y,
    ' ': lambda x, y: x & y,
    ':': lambda x, y: x + y
}.items()})
