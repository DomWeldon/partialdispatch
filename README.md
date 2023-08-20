# partialdispatch

_Function-level logic inspired by python's own `functools.singledispatch`._

## Requirements

* Python 3.8+

_The `Literal` typing annotation was only introduced in Python 3.8, after [PEP 586](https://peps.python.org/pep-0586/) was accepted._

## Edge Cases

Some values are illegal when used with the `typing.Literal` annotation, including those listed below.

* Complex numbers like `4 + 3j` 
* Literal values of types like `typing.Mapping` or `str`

To register an implementation for one of these values, supply the value as the first argument to the `register` function, instead of simply using the decorator. If the value is a `type`, then the keyword argument `literal` must evaluate to `True`.

## Testing

### Requirements

This project uses some tests from the [standard library's `test` module](https://docs.python.org/3/library/test.html), to check the interface of `partialdispatch.singledispatch_literal` for regression or unexpected differences from [the standard library's `functools.singledispatch`](https://docs.python.org/3/library/functools.html#functools.singledispatch). However, [since python 3.10](https://docs.python.org/3/whatsnew/3.10.html#build-changes), the `test` no longer contains most unit tests by default, and instead the `--enable-test-modules` flag must be included when python is installed, or else these tests will fail with a message like the below.


    ImportError while importing test module '/partialdispatch/tests/stdlib/functools/test_stdlib.py'.
    Hint: make sure your test modules/packages have valid Python names.
    Traceback:
    /usr/lib/python3.10/importlib/__init__.py:126: in import_module
        return _bootstrap._gcd_import(name[level:], package, level)
    tests/stdlib/functools/test_stdlib.py:1: in <module>
        from test.test_functools import TestSingleDispatch
    E   ModuleNotFoundError: No module named 'test.test_functools'


To overcome this issue and meet this requirement, we use the [`PYTHON_CONFIGURE_OPTS` environment variable](https://github.com/pyenv/pyenv/blob/master/plugins/python-build/README.md#special-environment-variables) when installing the required versions of python using [pyenv](https://github.com/pyenv/pyenv). This is configured by default [if using direnv](https://direnv.net/) by the following line in `.envrc`.

    PYTHON_CONFIGURE_OPTS="--enable-test-modules"