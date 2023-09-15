import functools
import sys
from test.test_functools import TestSingleDispatch as _TestSingleDispatch
from unittest import mock

import pytest

import partialdispatch

patched_func = mock.patch.object(
    functools,
    "singledispatch",
    functools.singledispatch,
)(partialdispatch.singledispatch_literal)


@mock.patch.object(functools, "singledispatch", patched_func)
class TestSingleDispatchLiteralAgainstStdLib(_TestSingleDispatch):
    ...


# some tests will fail or should be skipped
VERSION_TEST_MARKS_MAP = {
    # list them by python versions
    ((3, 8), (3, 12)): {
        "test_callable_register": [pytest.mark.xfail],
        "test_classmethod_register": [pytest.mark.xfail],
        "test_invalid_positional_argument": [pytest.mark.xfail],
        "test_staticmethod_register": [pytest.mark.xfail],
        "test_type_ann_register": [pytest.mark.xfail],
        "test_invalid_registrations": [
            pytest.mark.skip(reason="Not valid - rewrite to flip assertions.")
        ],
    },
    ((3, 9), (3, 12)): {
        "test_classmethod_type_ann_register": [pytest.mark.xfail],
        "test_staticmethod_type_ann_register": [pytest.mark.xfail],
        "test_double_wrapped_methods": [pytest.mark.xfail],
        "test_method_wrapping_attributes": [pytest.mark.xfail],
        # it is simply not possible to pass this test and
        # `test_register_genericalias`, whilst also passing
        # `test_register_genericalias_decorator`
        # "test_register_genericalias_annotation": [pytest.mark.xfail],
    },
}

# get relevant sets of marks (each a dict)
test_marks = [
    test_marks_map
    for (lower_v, upper_v), test_marks_map in VERSION_TEST_MARKS_MAP.items()
    if sys.version_info >= lower_v and sys.version_info <= upper_v
]

# call them on relevant tests
for markset in test_marks:
    for test, marks in markset.items():
        method = getattr(TestSingleDispatchLiteralAgainstStdLib, test)
        for mark in marks:
            method = mark(method)
        setattr(TestSingleDispatchLiteralAgainstStdLib, test, method)

__all__ = ["TestSingleDispatchLiteralAgainstStdLib"]
