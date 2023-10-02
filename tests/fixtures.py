import pytest

from kataria import Iterable, NativeIterable, Option, Result

from .utils import CallCounted


@pytest.fixture
def call_counted():
    return CallCounted(lambda *a, **k: None)


@pytest.fixture
def nothing() -> Option:
    return Option.Nothing()


@pytest.fixture
def something() -> Option:
    return Option.Something("meow")


@pytest.fixture
def another_thing() -> Option:
    return Option.Something(42)


@pytest.fixture
def ok() -> Result:
    return Result.Ok("meow")


@pytest.fixture
def err() -> Result:
    return Result.Err("fuck")


@pytest.fixture
def fine() -> Result:
    return Result.Ok("fine")


@pytest.fixture
def finite_iter() -> Iterable:
    return NativeIterable(range(10))


@pytest.fixture
def infinite_iter() -> Iterable:
    def infinite():
        i = 0
        while True:
            yield i
            i += 1

    return NativeIterable(infinite())
