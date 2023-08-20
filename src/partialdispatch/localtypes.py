"""Local types used in the project."""
import typing

AnnotationType = typing.Union[
    type,
    typing._GenericAlias,
    typing._SpecialForm,
]

__all__ = ["AnnotationType"]
