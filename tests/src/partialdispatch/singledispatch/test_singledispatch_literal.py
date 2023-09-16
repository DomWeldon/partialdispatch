import typing
from unittest import mock

import pytest

import partialdispatch.singledispatch as mod


def test__singledispatch_literal__error_on_invalid_sig():
    """Check a TypeError is raised when sig not valid."""

    # arrange
    def invalid_sig_func(*, a: int = 1, b: str = "1") -> str:
        return b * a

    # act
    with pytest.raises(TypeError) as e:
        mod.singledispatch_literal(invalid_sig_func)

    message = e.exconly()

    # assert
    assert "Invalid function passed" in message
    assert "Change argument 'a: int = 1' to be positional" in message
    assert invalid_sig_func.__name__ in message


def test__singledispatch_literal__error_when_called_kwargs_only():
    """Check that a TypeError is raised when no positional args passed"""
    # arrange
    func = mod.singledispatch_literal(lambda x, y: (x, y))
    expected_msg = "<lambda> requires at least 1 positional argument"

    # act
    with pytest.raises(TypeError) as e:
        func(x=1, y=2)

    msg = str(e)

    # assert
    assert expected_msg in msg


def test__is_literal_annotation__delayed_annos_positive():
    """Can it use literal annotations?"""


@pytest.mark.parametrize(
    ("annotation",),
    [
        (typing.Literal[1, 2],),
        (typing.Literal["a"],),
        (typing.Literal[None],),
        (typing.Optional[typing.Literal[1]],),
        (typing.Union[typing.Literal[1, 2], typing.Literal[3, 4]],),
        (
            typing.Union[
                typing.Union[typing.Literal[1, 2], typing.Literal[3, 4]],
                typing.Literal[1, 2],
                typing.Literal[1],
            ],
        ),
    ],
)
def test__is_literal_annotation__positive(annotation):
    """Check a bunch of test cases for Literal annotations."""
    # assert
    assert mod.is_literal_annotation(annotation) is True


@pytest.mark.parametrize(
    ("annotation",),
    [
        (typing.Union[str, int],),
        (str,),
        (typing.Callable,),
        (typing.Union[typing.Literal[1, 2], str],),
        (
            typing.Union[
                typing.Union[typing.Literal[1, 2], typing.Literal[3, 4]],
                typing.Literal[1, 2],
                str,
                typing.Literal[1],
            ],
        ),
    ],
)
def test__is_literal_annotation__negative(annotation):
    """Check a bunch of test cases for Literal annotations."""
    # assert
    assert mod.is_literal_annotation(annotation) is False


@pytest.mark.parametrize(
    (
        "annotation",
        "values",
    ),
    [
        [typing.Literal[1], {1}],
        [typing.Literal[None], {None}],
        [typing.Optional[typing.Literal["abc"]], {None, "abc"}],
        [typing.Literal[1, 2], {1, 2}],
        [typing.Union[typing.Literal[1], typing.Literal[2, 3]], {1, 2, 3}],
    ],
)
def test__flatten_literal_annotation__positive(annotation, values):
    """Check that values are extracted from Literal annotations"""
    # assert
    assert mod.flatten_literal_params(annotation) == values


def test__singledispatch_literal__error_on_kwonly():
    """Check matches stdlib behaviour requiring posiitonal arg."""

    # arrange
    def kwonly_func(*, a):
        return a

    # act
    with pytest.raises(TypeError) as e:
        mod.singledispatch_literal(kwonly_func)

    # assert
    assert "Invalid function passed" in str(e.value)
    assert "Function kwonly_func cannot take any positional" in str(e.value)


def test__singledispatch_literal__register__error_on_kwonly():
    """Check matches stdlib behaviour requiring posiitonal arg."""

    # arrange
    @mod.singledispatch_literal
    def func(a):
        pass

    # act
    with pytest.raises(TypeError) as e:

        @func.register
        def kwonly_reg(*, a):
            return a

    # assert
    assert "Invalid function passed" in str(e.value)
    assert "Function kwonly_reg cannot take any positional" in str(e.value)


def test__singledispatch_literal__register__error_on_no_anno():
    """Check raises error when first param not annotated for register."""

    # arrange
    @mod.singledispatch_literal
    def func(a):
        pass

    # act
    with pytest.raises(TypeError) as e:

        @func.register
        def noreg(a):
            return a

    # assert
    assert "Invalid function passed to register" in str(e.value)
    assert "The first argument of noreg, a, must be annotated" in str(e.value)


def test__singledispath_literal__dispatches_calls():
    """Example integration test of desired functionality"""
    # arrange
    mocks = {
        str: mock.Mock(),
        "abc": mock.Mock(),
        123: mock.Mock(),
    }

    @mod.singledispatch_literal
    def func(a):
        mocks[str](a)

    @func.register
    def _(a: typing.Literal["abc"]):
        mocks["abc"](a)

    @func.register(123)
    def _(a):
        mocks[123](a)

    # act
    for val in mocks:
        func(val)

    # assert
    for val, mock_ in mocks.items():
        mock_.assert_called_once_with(val)


def test__singledispatch_literal__can_take_callable():
    """Check it can take a callable when literal is true"""
    # arrange
    target = mock.Mock()
    not_target = mock.Mock()
    b = 1

    @mod.singledispatch_literal
    def example_func(a, b: int):
        raise Exception("I should not be called")

    @example_func.register
    def _(a: str, b: int):
        not_target(a, b)

    def some_cble():
        ...

    # act
    @example_func.register(some_cble, literal=True)
    def _target(a, b):
        target("hit target", b)

    example_func(some_cble, b)
    example_func("a", b)

    # assert
    target.assert_called_once_with("hit target", b)
    not_target.assert_called_once_with("a", b)


def some_cble():
    ...


@pytest.mark.parametrize(
    ("target_val",),
    [
        (some_cble,),
        (str,),
    ],
)
def test__singledispatch_literal__can_take_type(target_val):
    """Check it can take a type when literal is true"""
    # arrange
    target = mock.Mock()
    not_target = mock.Mock()
    b = 1

    @mod.singledispatch_literal
    def example_func(a, b: int):
        raise Exception("I should not be called")

    @example_func.register
    def _(a: str, b: int):
        not_target(a, b)

    # act
    @example_func.register(target_val, literal=True)
    def _target(a: type, b):
        target("hit target", b)

    example_func(target_val, b)
    example_func("a", b)

    # assert
    target.assert_called_once_with("hit target", b)
    not_target.assert_called_once_with("a", b)


@pytest.mark.parametrize(
    ("target_val",),
    [
        (lambda a, b: (a, b),),
    ],
)
def test__singledispatch_literal__raises_warning_on_lambda(target_val):
    """Check it can take a type when literal is true"""
    # arrange
    target = mock.Mock()
    not_target = mock.Mock()
    b = 1

    @mod.singledispatch_literal
    def example_func(a, b: int):
        raise Exception("I should not be called")

    @example_func.register
    def _(a: str, b: int):
        not_target(a, b)

    # act
    with pytest.warns():

        @example_func.register(target_val, literal=True)
        def _target(a, b):
            target("hit target", b)

    example_func(target_val, b)
    example_func("a", b)

    # assert
    target.assert_called_once_with("hit target", b)
    not_target.assert_called_once_with("a", b)
