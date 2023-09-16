import functools
import sys
from test.test_functools import TestSingleDispatch as _TestSingleDispatch
from unittest import mock

import pytest

import partialdispatch

# Create patched versions of partialdispatch.singledispatch and
# partialdispatch.singledispatchmethod, where the functools versions of these
# functions (still) point to the standard library implementations.
patched_singledispatch = mock.patch.object(
    functools,
    "singledispatch",
    functools.singledispatch,
)(partialdispatch.singledispatch_literal)
patched_singledispatchmethod = mock.patch.object(
    functools,
    "singledispatchmethod",
    functools.singledispatchmethod,
)(partialdispatch.singledispatchmethod_literal)


# However, in the standard library test module where stdlib tests live, patch
# the original functools.singledispatch and functools.singledispatchmethod
# names/addresses so that they now point to the patched functions we created
# above.
# This means that in the test module, singledispatch and singledispatchmethod
# refer to our implementation, and so it's our implementation that gets tested
# by the standard library tests, but inside our code, we still point back to
# the standard library versions, meaning we can use the original functions as
# required, and we don't accidentally recurse through patches.
@mock.patch.object(functools, "singledispatch", patched_singledispatch)
@mock.patch.object(
    functools, "singledispatchmethod", patched_singledispatchmethod
)
class TestSingleDispatchLiteralAgainstStdLib(_TestSingleDispatch):
    ...


xfail_strict = functools.partial(pytest.mark.xfail, strict=True)

# some tests will fail or should be skipped
VERSION_TEST_MARKS_MAP = {
    # list them by python versions
    ((3, 8), (3, 13)): {
        "test_callable_register": [xfail_strict],
        "test_classmethod_register": [xfail_strict],
        "test_invalid_positional_argument": [xfail_strict],
        "test_staticmethod_register": [xfail_strict],
        "test_type_ann_register": [xfail_strict],
        "test_invalid_registrations": [
            pytest.mark.skip(reason="Not valid - rewrite to flip assertions.")
        ],
    },
    ((3, 9), (3, 13)): {
        "test_classmethod_type_ann_register": [xfail_strict],
        "test_staticmethod_type_ann_register": [xfail_strict],
        "test_double_wrapped_methods": [xfail_strict],
        "test_method_wrapping_attributes": [xfail_strict],
        # it is simply not possible to pass this test and
        # `test_register_genericalias`, whilst also passing
        # `test_register_genericalias_decorator`
        # "test_register_genericalias_annotation": [xfail_strict],
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
