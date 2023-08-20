"""Check required behaviours of typing module."""
import inspect
import sys
import typing

import pytest


@pytest.mark.skipif(
    sys.version_info < (3, 9),
    reason="Type of Literal in 3.8 is simply _GenericAlias",
)
def test_isinstance_with_literal_generic_alias():
    """Can we check that parameters are literals using isinstance?"""

    # arrange
    def f(a: typing.Literal["a", "b"]):
        return a

    # act
    sig = inspect.signature(f)

    # assert
    assert isinstance(
        sig.parameters["a"].annotation, typing._LiteralGenericAlias
    )


@pytest.mark.skipif(
    sys.version_info >= (3, 9),
    reason="Type of Literal in 3.8 is simply _GenericAlias",
)
def test_isinstance_with_generic_alias():
    """Can we check that parameters are literals using isinstance?"""

    # arrange
    def f(a: typing.Literal["a", "b"]):
        return a

    # act
    sig = inspect.signature(f)

    # assert
    assert isinstance(sig.parameters["a"].annotation, typing._GenericAlias)


def test_literal_with_origin():
    """Can we check that parameters are literals using __origin__?"""

    # arrange
    def f(a: typing.Literal["a", "b"]):
        return a

    # act
    sig = inspect.signature(f)

    # assert
    assert sig.parameters["a"].annotation.__origin__ is typing.Literal


@pytest.mark.parametrize(
    (
        "cls",
        "args",
    ),
    [(typing.Union[str, int], (str, int)), (typing.Literal[1, 2], (1, 2))],
)
def test_generic_args_available(cls, args):
    """Can we use the __args__ attribute to get values from these types?"""
    # assert
    assert cls.__args__ == args
