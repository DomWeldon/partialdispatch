"""Tests illustratign what partialdispatch aims to do."""
import functools
import sys
import types
import typing

import pytest


def test__singledispatch__no_support_literals():
    """Demonstrate that singledispatch does not support Literals."""
    # arrange
    msg = "I don't want to run this code"

    @functools.singledispatch
    def f(a: int):
        raise Exception(msg)

    # act
    with pytest.raises(TypeError) as e:

        @f.register
        def _(a: typing.Literal[1]):
            return a

    # assert
    assert "typing.Literal[1] is not a class" in str(e)


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="typing.LiteralString only intrudced in Python 3.11",
)
def test__singledispatch__no_support_literalstrings():
    """Demonstrate that singledispatch does not support LiteralStrings."""
    # arrange
    msg = "I don't want to run this code"

    @functools.singledispatch
    def f(a: int):
        raise Exception(msg)

    # act
    with pytest.raises(TypeError) as e:

        @f.register
        def _(a: typing.LiteralString):
            return a

    # assert
    assert "typing.LiteralString is not a class" in str(e)


def test__singledispatch__single_value_types():
    """Check singledispatch with single-value types."""

    # arrange
    @functools.singledispatch
    def f(a):
        return "default"

    @f.register
    def _(a: int):
        return "int"

    # act
    @f.register
    def _(a: None):
        return "None"

    expect_int = f(1)
    expect_none = f(None)
    expect_default = f("a")
    expect_ellipsis = f(...)

    # assert
    assert expect_int == "int"
    assert expect_none == "None"
    assert expect_default == "default"
    assert expect_ellipsis == "default"


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="EllipsisType only introduced in 3.10",
)
def test__singledispatch__ellipsis():
    """Check singledispatch handles ellipsis"""

    # arrange
    @functools.singledispatch
    def f(a):
        return "default"

    @f.register
    def _(a: int):
        return "int"

    # act
    @f.register
    def _(a: types.EllipsisType):
        return "ellipsis"

    expect_int = f(1)
    expect_default = f("a")
    expect_ellipsis = f(...)

    # assert
    assert expect_int == "int"
    assert expect_default == "default"
    assert expect_ellipsis == "ellipsis"
