"""Some assertions about inspect and callables.

These are useful for checking assumptions across different python versions.
"""
import inspect

import pytest


@pytest.mark.parametrize(
    ("descriptor",),
    [
        (classmethod,),
        (staticmethod,),
    ],
)
def test_descriptormethods_are_callable_after_definition(descriptor):
    """Assert that descriptor methods are callable objects."""

    # arrange
    class A:
        def __init__(self, arg):
            self.arg = arg

        @descriptor
        def t(cls, arg):
            return cls("base")

    # act
    is_callable = callable(A.t)

    # assert
    assert is_callable is True


# @pytest.mark.skipif(
#     sys.version_info < (3, 10),
#     reason="classmethods not callable prior to 3.10, see bpo-43682"
# )
@pytest.mark.parametrize(
    ("descriptor",),
    [
        (classmethod,),
        (staticmethod,),
    ],
)
def test_descriptormethods_have_signatures_on_func(descriptor):
    """Assert that descriptor methods are not callable until class defined."""

    # arrange
    def try_get_sig(cble):
        inspect.signature(cble.__func__)

        return cble

    class A:
        def __init__(self, arg):
            self.arg = arg

        @try_get_sig
        @descriptor
        def t(cls, arg):
            return cls("base")


@pytest.mark.parametrize(
    ("descriptor",),
    [
        (classmethod,),
        (staticmethod,),
    ],
)
def test_descriptormethods_have_sigs(descriptor):
    """Assert that descriptor methods are not callable objects."""

    # arrange
    class A:
        def __init__(self, arg):
            self.arg = arg

        @classmethod
        def t(cls, arg):
            return cls("base")

    # act
    sig = inspect.signature(A.t)

    # assert
    assert sig is not None
    assert len(sig.parameters) == 1
    assert "arg" in sig.parameters
