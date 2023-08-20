"""Tests illustratign what partialdispatch aims to do."""
import functools
import sys
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
