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

@func.register(int, literal=True)
def _(a, b):

    return f"Literally, int! {a=}, {b=}"


vals = [
    123,
    "some string",
    49,
    Pet.Cat,
    Pet.Dog,
    Pet.Shark,
    int,
    None,
]

for v in vals:
    output = func(v, None)
    fmt = ("[yellow]", "[/yellow]") if _use_rich else ("", "")
    print(f"Calling func with {v}: {fmt[0]}{output}{fmt[1]}")