"""Check required behaviours of typing module."""
import inspect
import sys
import types
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


def test_union_literals():
    """Proove unions of literals are Union"""
    # arrange
    lit_union = typing.Union[typing.Literal[1], typing.Literal[2]]

    # assert
    assert lit_union.__origin__ is typing.Union


@pytest.mark.skipif(
    sys.version_info <= (3, 10),
    reason="Special forms introduced in 3.10",
)
def test_literal_special_forms_are_union_others_not():
    """Proove that special-form unions of Literal are Union"""
    # arrange
    lit_sf = typing.Literal[1] | typing.Literal[2]
    other_sf = float | str

    # assert
    assert lit_sf.__origin__ == typing.Union
    assert isinstance(other_sf, types.UnionType)


def test_literal_types_are_not_types():
    """Proove that instances of literal are not types"""
    # arrange
    lit = typing.Literal[1]

    # assert
    assert not isinstance(lit, type)


@pytest.mark.parametrize(
    ("anno_type",),
    [
        (typing.Union[str, float],),
        (typing.Optional[float],),
    ],
)
def special_unions_are_not_types(anno):
    """Proove that a Union is not a type"""
    assert not isinstance(anno, type)


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
