[![Python 3.8+](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


# partialdispatch

This project is currently under development, with a release of a partialdispatch function expected soon. If you're interested in it, please get in touch, but but be aware this is very much "building in (semi)-public", until a proper documented version is up.

Currently, the only supported function is `partialdispatch.singledispatch_literal`, which implements the functionality of [functools.singledispatch](https://docs.python.org/3/library/functools.html#functools.singledispatch) for [literal types](https://docs.python.org/3/library/functools.html#functools.singledispatch) and values, including [enums](https://docs.python.org/3/library/enum.html).

## `partialdispatch.singledispatch_literal`

Transform a function into a sing-dispatch generic function, which also supports dispatching to a different callable based on a literal value.

Literal values are specified using either the [typing.Literal](https://docs.python.org/3/library/typing.html#typing.Literal) type annotation, a literal [type such as an `enum`](https://docs.python.org/3/library/enum.html), or by passing the keyword argument `literal=True` to the `register` function.

The example below shows how this function can be used. The code should run "as-is" (and will use rich to print in colour if you have it on your system or in your virtualenv).

```python
import enum
import typing

import partialdispatch

_use_rich = None
try:
    import rich
except ModuleNotFoundError:
    pass
    _use_rich = False
else:
    _use_rich = True
    print = rich.print

class Pet(enum.Enum):
    Cat: str = "🐱"
    Dog: str = "🐕"
    Shark: str = "🦈"

@partialdispatch.singledispatch_literal
def func(a, b):

    return f"default: {a=}, {b=}"

@func.register
def _(a: int, b):

    return f"int: {a=}, {b=}"

@func.register
def _(a: typing.Literal[49], b):

    return f"The meaning of life {a=}, {b=}"

@func.register
def _(a: Pet.Cat, b):

    return f"meow! {a=}, {b=}"


@func.register(Pet.Dog, literal=True)
def _(a, b):

    return f"Good boy! {a=}, {b=}"


vals = [
    123,
    "some string",
    49,
    Pet.Cat,
    Pet.Dog,
    Pet.Shark,
    None,
]

for v in vals:
    output = func(v, None)
    fmt = ("[yellow]", "[/yellow]") if _use_rich else ("", "")
    print(f"Calling func with {v}: {fmt[0]}{output}{fmt[1]}")
```


Drawbacks

* Currently only works on hash equality 

The argument `literal=True` must be passed when:

* Value is callable
* Value is a type
* Value is None