import pytest

from kataria import Option, Panic, Result

from .fixtures import another_thing, call_counted, err, nothing, ok, something
from .utils import CallCounted, assert_not_called


def test_Nothing(nothing):
    assert nothing._inner is None
    assert nothing.is_none()


def test_Nothing_unwrap_panic(nothing):
    with pytest.raises(Panic):
        nothing.unwrap()

    with pytest.raises(Panic):
        nothing.expect("fuck")


def test_Something(something):
    assert something.is_some()
    assert something.unwrap() == "meow"


def test_Something_unwrap(something):
    assert something.unwrap() == "meow"
    assert something.expect("fuck") == "meow"


def test_map(something, nothing):
    some = something.map(lambda v: v + v)
    none = nothing.map(assert_not_called)

    assert none == Option.Nothing()
    assert some.is_some()
    assert some.unwrap() == "meowmeow"


def test_is_some_none(something, nothing):
    assert something.is_some()
    assert nothing.is_none()
    assert something.is_some_and(lambda v: v == "meow")


def test_inspect(something, nothing, call_counted):
    nothing.inspect(assert_not_called)
    something.inspect(call_counted)
    assert call_counted.count == 1


def test_map_or(something, nothing):
    def mappy(_):
        return 2

    assert something.map_or(1, mappy) == 2
    assert nothing.map_or(1, mappy) == 1


def test_map_or_else(something, nothing):
    @CallCounted
    def default():
        return 1

    @CallCounted
    def mappy(_):
        return 2

    assert mappy == 0
    assert default == 0

    assert something.map_or_else(default, mappy) == 2
    assert mappy == 1

    assert nothing.map_or_else(default, mappy) == 1
    assert default == 1


def test_ok_or(something, nothing, ok, err):
    some = something.ok_or("fuck")
    none = nothing.ok_or("fuck")

    assert some == ok
    assert none == err


def test_ok_or_else(something, nothing, ok, err):
    some = something.ok_or_else(lambda: "fuck")
    none = nothing.ok_or_else(lambda: "fuck")

    assert some == ok
    assert none == err


def test_bool_and(something, nothing, another_thing):
    assert something.bool_and(another_thing).unwrap() == 42
    assert something.bool_and(nothing).is_none()
    assert nothing.bool_and(something).is_none()


def test_bool_or(something, nothing):
    assert something.bool_or(nothing) == nothing.bool_or(something)
    assert something.bool_or(nothing) == something
    assert nothing.bool_or(nothing).is_none()


def test_bool_xor(something, nothing):
    assert something.bool_xor(nothing) == something
    assert nothing.bool_xor(something) == something
    assert nothing.bool_xor(nothing) == nothing
    assert something.bool_xor(something) == nothing


def test_and_then(something, nothing, call_counted):
    assert nothing.and_then(assert_not_called) == nothing

    something.and_then(call_counted)
    assert call_counted == 1

    meow2 = something.and_then(lambda v: Option.Something(f"{v} {v}"))

    assert meow2.unwrap() == "meow meow"


def test_filter(something, nothing):
    nothing.filter(assert_not_called)

    assert something.filter(lambda _: False) == nothing
    assert something.filter(lambda _: True) == something


def test_or_else(something, nothing):
    assert something.or_else(assert_not_called) == something
    assert nothing.or_else(lambda: Option.Something(42)).unwrap() == 42
    assert nothing.or_else(lambda: Option.Nothing()) == nothing


def test_replace(something, nothing):
    old = something.replace(42)
    assert old.unwrap() == "meow"
    assert something.unwrap() == 42

    old2 = nothing.replace(42)
    assert old2.is_none()
    assert nothing.unwrap() == 42


def test_zip(something, nothing, another_thing):
    assert something.zip(nothing).is_none()
    assert nothing.zip(something).is_none()
    assert something.zip(another_thing).unwrap() == ("meow", 42)


def test_zip_with(something, nothing, another_thing):
    def fmt(a, b):
        return f"{b}, {a}"

    assert something.zip_with(nothing, fmt).is_none()
    assert nothing.zip_with(something, fmt).is_none()
    assert something.zip_with(another_thing, fmt).unwrap() == "42, meow"


def test_unzip(nothing, something):
    a, b = Option.Something(("meow", 42)).unzip()
    assert a.unwrap() == "meow"
    assert b.unwrap() == 42

    c, d = nothing.unzip()
    assert c.is_none()
    assert d.is_none()

    with pytest.raises(ValueError):
        something.unzip()

    with pytest.raises(TypeError):
        b.unzip()


def test_transpose(ok, err, nothing):
    some_ok = Option.Something(ok)
    some_err = Option.Something(err)

    assert nothing.transpose() == Result.Ok(nothing)
    assert some_ok.transpose() == Result.Ok(Option.Something("meow"))
    assert some_err.transpose() == Result.Err("fuck")


def test_flatten(something, nothing):
    nesty = Option.Something(something)
    assert nesty.flatten() == something
    assert nothing.flatten() == nothing
