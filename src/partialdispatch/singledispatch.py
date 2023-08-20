"""singledispatch_literal
----------------------
"""
import functools
import inspect
import itertools
import sys
import typing
import warnings

from .localtypes import AnnotationType

T = typing.TypeVar("T")

# ParamSpec was new in 3.10
if sys.version_info >= (3, 10):
    P = typing.ParamSpec("P")
else:
    P = ...


def is_literal_annotation(annotation: AnnotationType) -> bool:
    """Determine whether an annotation is an instance of typing.Literal.

    N.B. - `isinstance()` cannot be used with typing.Literal, a TypeError
    is raised if it is supplied as the type argument.
    """
    origin = getattr(annotation, "__origin__", None)

    if origin is typing.Literal:
        return True

    if origin is typing.Union:
        return all(is_literal_annotation(anno) for anno in annotation.__args__)

    return False


def flatten_literal_params(annotation: AnnotationType) -> set:
    """Flatten an annotation into a set of values."""
    if annotation.__origin__ is typing.Union:
        return set(
            itertools.chain.from_iterable(
                flatten_literal_params(a) for a in annotation.__args__
            )
        )

    return set(annotation.__args__)


def _check_has_pos_params(func: typing.Callable[P, T], sig: inspect.Signature):
    """Raise a TypeError if no args can be positional."""

    for arg in sig.parameters.values():
        if arg.kind is not inspect.Parameter.KEYWORD_ONLY:
            return

    name = func.__name__ if hasattr(func, "__name__") else "unknown function"
    first_param = next(iter(sig.parameters))

    raise TypeError(
        f"Invalid function passed to singledispatch_literal. Function {name} "
        "cannot take any positional arguments, singledispatch and "
        "singledispatch_literal pass the first argument positionally. Change "
        f"argument '{first_param}' to be positional only, or positional or "
        "keyword by moving the '*' at the start of its arguments."
    )


def _check_value_valid(value: typing.Any):
    """Check value is valid."""
    if callable(value) and getattr(value, "__name__", None) == "<lambda>":
        warnings.warn(
            "Using anonymous (lambda) functions as a dispatch value is not "
            "advised as two identical lambdas with the same arguments and "
            "are still different values when compared using == or is."
        )


def _check_first_pos_param_annotated(
    funcname: str, func: typing.Callable[P, T], sig: inspect.Signature
):
    """Check whether signature has enough args and annotations."""
    first_param = next(iter(sig.parameters.values()))
    if first_param.annotation is inspect._empty:
        name = (
            func.__name__ if hasattr(func, "__name__") else "unknown function"
        )

        raise TypeError(
            "Invalid function passed to register. The first argument of "
            f"{name}, {first_param.name}, must be annotated if no value/type "
            "was passed as the first argument to register. Annotate it, or "
            f"use @{funcname}.register(some_value) instead."
        )


def singledispatch_literal(f: typing.Callable[P, T]) -> typing.Callable[P, T]:
    """Wrapper around functools.stdlib supporting literal arguments."""
    # start inspecting function
    sig = inspect.signature(f)

    _check_has_pos_params(func=f, sig=sig)

    first_param = next(iter(sig.parameters))
    funcname = getattr(f, "__name__", "singledispatch_literal function")

    # determine that function is valid
    _check_has_pos_params(f, sig)

    # wrap it for type-based use
    stdlib_wrapped = functools.singledispatch(f)
    literal_registry = {}

    def dispatch(val: typing.Any) -> T:
        # is the value in the literal registry?
        if val in literal_registry:
            # yes, use the registered callable

            return literal_registry[val]

        # no, revert to the standard library implementation
        return stdlib_wrapped

    def register(
        value: typing.Any,
        func: typing.Optional[typing.Callable[P, T]] = None,
        literal: bool = False,
    ):
        """Register a new implementation for the given value or type.

        The function will first look to see if the first positional argument
        is annotated with a `typing.Literal`, and if so, register that value
        in the function's `literal_registry`. Otherwise, it passes the call on
        to the standard library's `functools.singledispatch` implementation of
        the `register` function, unless `literal` is `True`.

        If `literal=True` then this function registers the type's _literal_
        value against provided function, like below.


        >>> @singledispatch_literal
        >>> def some_func(a: int):
        >>>     '''Default implementation'''
        >>>     return f"{a} is an integer"

        >>> @some_func.register(str)
        >>> def _(a: str):
        >>>     return f"{a} is a string"

        >>> @some_func.register(str, literal=True)
        >>> def _(a: type):
        >>>     return f"{a} is the type 'str'"

        >>> some_func(1)
        "1 is an integer"

        >>> some_func("hello world")
        "hello world is a string"

        >>> some_func(str)
        "<class 'str'> is the type 'str'"

        Args:
            value: the type or literal value being registered
            func: the function to register the type or literal value to
            literal: when True, if a type is passed to `value`, the literal
                value of the type will be registered (see notes).
        """
        nonlocal literal_registry
        sig: inspect.Signature
        first_param: inspect.Parameter

        # func and value can become mixed up during decorator use
        if func is None:
            # Could be being called to register a single value or type on the
            # next callable, or being called as a decorator with no args to
            # register the annotation of the first param.

            if (
                # e.g. @func.register(int)
                (not callable(value) and not literal)
                or
                # e.g. @func.register(some_func, literal=True)
                (callable(value) and literal)
            ):
                # function called with a value argument only
                # return decorator to get the function in next pass

                return lambda f: register(value, func=f, literal=literal)

            value, func = None, value

        sig = inspect.signature(func)

        # check we're valid to continue
        _check_has_pos_params(func, sig)
        first_param = next(iter(sig.parameters.values()))

        if value is None:
            # get the annotation
            _check_first_pos_param_annotated(funcname, func, sig)
            value = first_param.annotation

        # is the value a literal?
        if is_literal_annotation(value):
            # check valid and put into the literal registry
            for val in flatten_literal_params(value):
                _check_value_valid(val)

                literal_registry[val] = func

            return f

        if literal or not isinstance(value, type):
            _check_value_valid(value)
            literal_registry[value] = func

            return f

        # no, pass it onto the stdlib
        return stdlib_wrapped.register(value, func)

    def wrapper(*args, **kwargs):
        # check that positional arguments were provided
        if not args:
            val = kwargs.get(first_param) or "123"

            raise TypeError(
                "When used with singledispatch or singledispatch_literal, "
                f"{funcname} requires at least one argument, {first_param}, "
                "to be passed positionally. Try calling the function like "
                f"{funcname}({val}, ...) instead of "
                f"{funcname}({first_param}={val})."
            )

        return dispatch(args[0])(*args, **kwargs)

    # add new attributes to wrapper function
    wrapper.literal_registry = literal_registry
    wrapper.register = register
    wrapper.dispatch = dispatch

    # update signature and wrapper
    functools.update_wrapper(wrapper=wrapper, wrapped=f)

    return wrapper
