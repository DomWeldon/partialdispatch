"""Single Dispatcher Functions
---------------------------

This module 
"""
import functools
import inspect
import itertools
import sys
import types
import typing
import warnings

T = typing.TypeVar("T")

# 3.10 introduced types.UnionType, used for annotations like `str | list`
if sys.version_info >= (3, 10):
    TYPES = (
        type,
        types.EllipsisType,
        types.NoneType,
    )
    GENERIC_TYPES = (
        typing._GenericAlias,
        types.GenericAlias,
        types.UnionType,
        typing._UnionGenericAlias,
        typing._LiteralGenericAlias,
    )
    SPECIAL_FORMS = (typing._SpecialForm,)
elif sys.version_info >= (3, 9):
    TYPES = (type,)
    GENERIC_TYPES = (
        typing._GenericAlias,
        types.GenericAlias,
    )
    SPECIAL_FORMS = (typing._SpecialForm,)
# GenericAlias was introduced in 3.8
elif sys.version_info[:2] == (3, 8):
    TYPES = (type,)
    GENERIC_TYPES = (typing._GenericAlias,)
    SPECIAL_FORMS = (typing._SpecialForm,)
else:
    major, minor = sys.version_info[:2]
    raise RuntimeError(
        "partialdispatch does not support Python {major}.{minor}"
    )

# ParamSpec was new in 3.10
if sys.version_info >= (3, 10):
    P = typing.ParamSpec("P")
else:
    P = ...


def _get_signature(cble: typing.Callable) -> inspect.Signature:
    """Get signature from callable, including descriptors prior to 3.10.

    Prior to python 3.10 descriptor protocol objects, like methods decorated
    with staticmethod or classmethod, were not callable (see bpo-43682).
    """
    # are we trying to get a class/staticmethod in 3.8 or 3.9?
    if (
        sys.version_info <= (3, 10) and isinstance(cble, (staticmethod))
    ) or isinstance(cble, classmethod):
        # Yes. Here we use a workaround of the descriptor protocol to simply
        # get the underlying callable. We do not know what the correct class
        # to provide here is, but since we won't be calling the callable, we
        # can just provide object, allowing us to get a signature.

        return inspect.signature(cble.__func__)

    return inspect.signature(cble)


def is_typey(obj: typing.Any) -> bool:
    """Does this object appear to be a type or special form?"""

    return isinstance(obj, TYPES + GENERIC_TYPES + SPECIAL_FORMS)


def is_literal_annotation(
    annotation: typing.Union[typing._SpecialForm, type]
) -> bool:
    """Determine whether an annotation is a literal.

    N.B. - `isinstance()` cannot be used with typing.Literal, a TypeError
    is raised if it is supplied as the type argument.
    """
    if annotation is type(None) or annotation is None:
        return True

    origin = getattr(annotation, "__origin__", None)

    if origin is typing.Literal:
        return True

    if origin is typing.Union:
        return all(is_literal_annotation(anno) for anno in annotation.__args__)

    return False


def flatten_literal_params(annotation: typing._SpecialForm) -> set:
    """Flatten an annotation into a set of values."""
    if annotation is type(None):
        return {None}

    if annotation.__origin__ is typing.Union:
        return set(
            itertools.chain.from_iterable(
                flatten_literal_params(a) for a in annotation.__args__
            )
        )

    return set(
        arg if arg is not type(None) else None for arg in annotation.__args__
    )


def _get_first_param(
    func: typing.Callable,
    sig: inspect.Signature,
    is_method: bool,
) -> inspect.Parameter:
    """Get relevant first parameter for singledispatch."""
    params = iter(sig.parameters.values())

    # is it a method?
    if not isinstance(func, staticmethod) and is_method:
        # yes, skip the first param
        _ = next(params)

    return next(params)


def _check_has_pos_params(
    func: typing.Callable[P, T], sig: inspect.Signature, is_method: bool
):
    """Raise a TypeError if no args can be positional."""
    i = 0
    for arg in sig.parameters.values():
        # is it a classmethod?
        if i == 0 and isinstance(func, classmethod):
            # yes, skip the cls param
            i += 1
            continue

        if arg.kind is not inspect.Parameter.KEYWORD_ONLY:
            return

    name = func.__name__ if hasattr(func, "__name__") else "unknown function"
    first_param = _get_first_param(func, sig, is_method=is_method)

    raise TypeError(
        f"Invalid function passed to singledispatch_literal. Function {name} "
        "cannot take any positional arguments, singledispatch and "
        "singledispatch_literal pass the first argument positionally. Change "
        f"argument '{first_param}' to be positional only, or positional or "
        "keyword by moving the '*' at the start of its arguments."
    )


def _warn_value_unlikely(value: typing.Any):
    """Check for highly unlikely values."""

    if callable(value) and getattr(value, "__name__", None) == "<lambda>":
        warnings.warn(
            "Using anonymous (lambda) functions as a dispatch value is not "
            "advised as two identical lambdas with the same arguments and "
            "are still different values when compared using == or is."
        )


def _valid_union(value: typing.Any, passed_as_annotation: bool) -> bool:
    """Is the Union value valid?"""
    if not (
        sys.version_info >= (3, 11)
        and passed_as_annotation
        and isinstance(value, (types.UnionType, typing._UnionGenericAlias))
    ):
        return False

    return all(isinstance(a, TYPES) for a in value.__args__)


def _check_value_valid(
    value: typing.Any,
    func: typing.Optional[typing.Callable[P, T]],
    stdlib_wrapped: typing.Callable[P, T],
    passed_as_annotation: bool,
) -> typing.Optional[bool]:
    """Check value is valid for either literal or stdlib

    GenericAlias types are not allowed for use with singledispatch. However,
    singledispatch_literal allows the use of typing.Literal, and the use of
    typing.Union types, where all possible members are also Literal.

    We also allow the use of the Literal values of these special types, when

    """
    if is_literal_annotation(value):
        # If these are passed, then we allow register to continue.
        # These values could still be invalid, but if they are, we'll
        # raise the error the second time this function is called,
        # in order to raise a more informative error message with the
        # function name in it.

        return True

    if not is_typey(value):
        return True

    if isinstance(value, GENERIC_TYPES + SPECIAL_FORMS):
        # https://docs.python.org/3/whatsnew/3.11.html#functools
        # Python 3.11 added support for types.UnionType annotations
        # (e.g., `str | int`) in singledispatch, so we don't need to raise the
        # error below in such instances when it was passed as an annotation
        if _valid_union(value, passed_as_annotation):
            return True

        try:
            stdlib_wrapped.register(value)
        except TypeError as e:
            func_name = stdlib_wrapped.__name__

            required_message = (
                "Invalid annotation for 'arg' on the function passed to"
                if passed_as_annotation
                else "Invalid first argument to"
            )

            if passed_as_annotation:
                e.args = (
                    f"{required_message} register(): {value} is not a class",
                ) + e.args[1:]

            raise TypeError(
                "The standard library functools.singledispatch is raising "
                f"this TypeError because of an {required_message} "
                "the register method. GenericAlias annotations such as "
                f"{value} cannot be used as types by the standard library's "
                "functools.standard_dispatch. If you want to use the literal "
                f"value of this type, such that {func_name}({value}) would "
                f"call {func}({value}), then pass the literal=True keyword "
                "argument to register: "
                f"i.e. @{func_name}.register({value}, literal=True) ."
                "See the full traceback for the original exception."
            ) from e

        else:
            func_name = stdlib_wrapped.__name__

            raise RuntimeError(
                "singledispatch_literal expected the standard library "
                f"implementation to raise a TypeError with this value: "
                f"{value}`. However, when it called it using"
                f" `{func_name}.register()` no TypeError was raised. This is "
                "an error in partialdispatch.singledispatch_literal, not your"
                " code. Please report it to the maintainers on GitHub: "
                "https://github.com/DomWeldon/partialdispatch/issues/new"
            )

        return True


def _signal_passed_as_annotation(
    f: typing.Callable[P, T]
) -> typing.Callable[P, T]:
    """Mark a function to show passed_as_annotation=True."""
    f._singledispatch_literal_annotated = True

    return f


def _check_passed_as_annotation(f: typing.Callable) -> bool:
    """Was the function passed as an annotation?"""
    try:
        return f._singledispatch_literal_annotated
    except AttributeError:
        return False


def _get_first_type_hint(
    func: typing.Callable, sig: inspect.Signature, is_method: bool
):
    first_param = _get_first_param(func=func, sig=sig, is_method=is_method)
    hints = (
        typing.get_type_hints(func)
        if not isinstance(func, (classmethod, staticmethod))
        else typing.get_type_hints(func.__func__)
    )

    return hints[first_param.name]


def _check_first_pos_param_annotated(
    funcname: str,
    func: typing.Callable[P, T],
    sig: inspect.Signature,
    is_method: bool,
):
    """Check whether signature has enough args and annotations."""
    first_param = _get_first_param(func=func, sig=sig, is_method=is_method)
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
    sig = _get_signature(f)

    # determine that function is valid
    is_method: bool = False
    _check_has_pos_params(func=f, sig=sig, is_method=is_method)
    first_param = next(iter(sig.parameters))
    funcname = getattr(f, "__name__", "singledispatch_literal function")

    # wrap it for type-based use
    stdlib_wrapped = functools.singledispatch(f)
    literal_registry = {}

    def _set_method(val: bool):
        """Used to set when used as a method"""
        nonlocal is_method

        # has the value changed?
        if is_method != val:
            # yes, check the validity of the base function again
            _check_has_pos_params(
                func=f,
                sig=sig,
                is_method=not is_method,
            )

        is_method = val

    def dispatch(
        val: typing.Any,
        literal: bool = False,
        passthru: bool = True,
    ) -> T:
        # are we allowing literal values?
        if literal:
            # yes, can we hash it?
            try:
                hash(val)
            except TypeError:
                # no
                pass
            else:
                # yes, is it in the registry?
                if val in literal_registry:
                    # yes, return this callable

                    return literal_registry[val]

            if not passthru:
                return None

        # no, revert to the standard library implementation
        return stdlib_wrapped.dispatch(val)

    def register(
        value: typing.Any,
        func: typing.Optional[typing.Callable[P, T]] = None,
        *,
        literal: bool = False,
    ) -> typing.Union[
        typing.Callable[P, T],
        typing.Callable[
            [typing.Any, typing.Callable[P, T], bool], typing.Callable[P, T]
        ],
    ]:
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
        passed_as_annotation: bool = _check_passed_as_annotation(func)

        # Is the decorator being called like
        # @f.register
        # or
        # @f.register(cble)  # where cble is a callable
        if func is None:
            # If the value passed to us is a generic, we check whether it's
            # definitely invalid at this stage, and raise an error matching
            # the standard library if it is.
            if is_typey(value) and not literal:
                _check_value_valid(
                    value=value,
                    stdlib_wrapped=stdlib_wrapped,
                    func=func,
                    passed_as_annotation=passed_as_annotation,
                )

            # we assume that type was passed
            # as annotation until told otherwise
            passed_as_annotation = False

            # is value our value, or func?
            if (
                literal  # value, user told us
                or is_literal_annotation(value)
                or is_typey(value)
                or (
                    not callable(value)
                    and not (
                        isinstance(value, classmethod)
                        or (
                            sys.version_info < (3, 10)
                            and isinstance(value, staticmethod)
                        )
                    )
                )
            ):
                # definitely our value, it was called like
                # @f.register(<SomeValueOrType>)
                return lambda f: register(
                    value,
                    func=_signal_passed_as_annotation(f),
                    literal=literal,
                )

            # definitely our func, called like @f.register
            value, func = None, value
            passed_as_annotation = True

        sig = _get_signature(func)

        # check we're valid to continue
        _check_has_pos_params(func=func, sig=sig, is_method=is_method)
        if value is None and not literal:
            # get the annotation
            _check_first_pos_param_annotated(
                funcname=funcname, func=func, sig=sig, is_method=is_method
            )
            value = _get_first_type_hint(
                func=func, sig=sig, is_method=is_method
            )

        # is the value a literal?
        if is_literal_annotation(value):
            # check valid and put into the literal registry
            for val in flatten_literal_params(value):
                _warn_value_unlikely(value)
                literal_registry[val] = func

            return f

        not_typey = not is_typey(value)

        # check value is valid, raising exception if so.
        # special_type tells us if it's a particular kind of type that we
        # support as a literal value
        _check_value_valid(
            value=value,
            stdlib_wrapped=stdlib_wrapped,
            func=func,
            passed_as_annotation=passed_as_annotation,
        )

        # it's not a literal annotation, is it a literal value?
        if literal or not_typey:
            # either user says it is, or it's not a type
            _warn_value_unlikely(value)
            literal_registry[value] = func

            return f

        # no, pass it onto the stdlib
        return stdlib_wrapped.register(value, func)

    def wrapper(*args, **kwargs):
        """Function that actually gets called."""
        # check that positional arguments were provided
        if not args:
            val = kwargs.get(first_param) or "123"

            raise TypeError(
                "When used with singledispatch or singledispatch_literal, "
                f"{funcname} requires at least 1 positional argument. "
                "Try calling the function like "
                f"{funcname}({val}, ...) instead of "
                f"{funcname}({first_param}={val})."
            )

        cble = dispatch(args[0], literal=True, passthru=False)

        if cble is not None:
            return cble(*args, **kwargs)

        return stdlib_wrapped(*args, **kwargs)

    # add new attributes to wrapper function
    wrapper.literal_registry = literal_registry
    wrapper.register = register
    wrapper.dispatch = dispatch
    wrapper.registry = stdlib_wrapped.registry
    wrapper._clear_cache = stdlib_wrapped._clear_cache
    wrapper._set_method = _set_method

    # update signature and wrapper
    functools.update_wrapper(wrapper=wrapper, wrapped=f)

    return wrapper


class singledispatchmethod_literal:
    """Single-dispatch generic with literal support, method descriptor.

    Supports wrapping existing descriptors and handles non-descriptor
    callables as instance methods.
    """

    def __init__(self, func: typing.Callable[P, T]):
        if not callable(func) and not hasattr(func, "__get__"):
            raise TypeError(f"{func!r} is not callable or a descriptor")

        self.dispatcher = singledispatch_literal(func)
        self.func = func
        self._wrapped_func = func

        if isinstance(
            func, (classmethod, staticmethod)
        ) and sys.version_info < (3, 10):
            self._wrapped_func = func.__func__

    def register(
        self,
        value: typing.Any,
        method=None,
        literal: bool = False,
    ) -> typing.Union[
        typing.Callable[P, T],
        typing.Callable[
            [
                "singledispatchmethod_literal",
                typing.Any,
                typing.Callable[P, T],
                bool,
            ],
            typing.Callable[P, T],
        ],
    ]:
        """Register the implementation for the given value or type."""
        self.dispatcher._set_method(True)

        return self.dispatcher.register(value, func=method, literal=literal)

    def __get__(self, obj, cls=None):
        """Descriptor wrapper around wrapper function."""

        def _method(*args, **kwargs):
            """Method equivalent of wrapper."""
            # check that args were provided
            if not args:
                # provide informative exception if not
                funcname = getattr(self.func, "__name__", f"{self.func}")
                try:
                    first_param = _get_signature(self.func).parameters[0].name
                except TypeError:
                    first_param = "unknown"

                val = kwargs.get(first_param) or "123"

                raise TypeError(
                    "When used with singledispatchmethod or "
                    f"singledispatchmethod_literal, {funcname} requires at "
                    f"least 1 positional argument. "
                    "Try calling the function like "
                    f"{funcname}({val}, ...) instead of "
                    f"{funcname}({first_param}={val})."
                )

            # try to dispatch literally
            method = self.dispatcher.dispatch(
                args[0], literal=True, passthru=False
            )
            if method is not None:
                return method.__get__(obj, cls)(*args, **kwargs)

            # dispatch by class
            method = self.dispatcher.dispatch(args[0].__class__)
            return method.__get__(obj, cls)(*args, **kwargs)

        _method.__isabstractmethod__ = self.__isabstractmethod__
        _method.register = self.register
        _method.registry = self.dispatcher.registry
        _method.literal_registry = self.dispatcher.literal_registry
        functools.update_wrapper(_method, self._wrapped_func)

        return _method

    @property
    def __isabstractmethod__(self):
        return getattr(self.func, "__isabstractmethod__", False)


__all__ = ["singledispatch_literal", "singledispatchmethod_literal"]
