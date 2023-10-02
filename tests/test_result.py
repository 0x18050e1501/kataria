import pytest

from kataria import Option, Panic, Result

from .fixtures import call_counted, err, fine, nothing, ok, something
from .utils import assert_not_called


def test_ok(ok):
    assert ok.is_ok()
    assert ok.is_ok_and(lambda v: v == "meow")
    assert not ok.is_err()
    assert not ok.is_err_and(assert_not_called)
    assert ok._value == "meow"


def test_err(err):
    assert err.is_err()
    assert err.is_err_and(lambda e: e == "fuck")
    assert not err.is_ok()
    assert not err.is_ok_and(assert_not_called)
    assert err._value == "fuck"


def test_ok_fn(ok, err, something, nothing):
    assert ok.ok() == something
    assert err.ok() == nothing


def test_err_fn(ok, err, nothing):
    something = Option.Something("fuck")

    assert ok.err() == nothing
    assert err.err() == something


def test_unwrap(ok, err):
    assert ok.unwrap() == "meow"
    with pytest.raises(Panic):
        err.unwrap()

    assert ok.expect("heck") == "meow"
    with pytest.raises(Panic):
        try:
            err.expect("heck")
        except Panic as e:
            assert "heck" in f"{e}"
            raise e


def test_unwrap_err(ok, err):
    with pytest.raises(Panic):
        ok.unwrap_err()
    assert err.unwrap_err() == "fuck"

    with pytest.raises(Panic):
        try:
            ok.expect_err("heck")
        except Panic as e:
            assert "heck" in f"{e}"
            raise e
    assert err.expect_err("heck") == "fuck"


def test_unwrap_or(ok, err):
    assert ok.unwrap_or(42) == "meow"
    assert err.unwrap_or(42) == 42


def test_unwrap_or_else(ok, err):
    assert ok.unwrap_or_else(assert_not_called) == "meow"
    assert err.unwrap_or_else(lambda e: f"{e}") == "fuck"


def test_map(ok, err):
    assert err.map(assert_not_called) == err
    assert ok.map(lambda v: v * 2).unwrap() == "meowmeow"


def test_map_or(ok, err):
    assert ok.map_or(42, lambda v: v * 2) == "meowmeow"
    assert err.map_or(42, assert_not_called) == 42


def test_map_or_else(ok, err):
    def get_default(e):
        return "fuck" in f"{e}"

    assert ok.map_or_else(get_default, lambda v: v * 2) == "meowmeow"
    assert err.map_or_else(get_default, assert_not_called)


def test_map_err(ok, err):
    assert ok.map_err(assert_not_called).unwrap() == "meow"
    assert err.map_err(lambda e: 42).unwrap_err() == 42


def test_inspect(ok, err, call_counted):
    ok.inspect(call_counted)
    err.inspect(assert_not_called)
    assert call_counted == 1

    ok.inspect_err(assert_not_called)
    err.inspect_err(call_counted)
    assert call_counted == 2


def test_bool_and(ok, err, fine):
    assert ok.bool_and(fine) == fine
    assert ok.bool_and(err) == err
    assert err.bool_and(ok) == err


def test_bool_or(ok, err, fine):
    assert ok.bool_or(fine) == ok
    assert err.bool_or(fine) == fine
    assert ok.bool_or(err) == ok
    assert err.bool_or(err) == err


def test_and_then(ok, err, fine):
    assert err.and_then(assert_not_called) == err
    assert ok.and_then(lambda t: fine) == fine
    assert ok.and_then(lambda t: err) == err


def test_or_else(ok, err):
    assert ok.or_else(assert_not_called) == ok
    assert err.or_else(lambda e: Result.Ok(e)).unwrap() == "fuck"


def test_transpose(err, something, nothing):
    ok_some = Result.Ok(something)
    ok_none = Result.Ok(nothing)

    assert ok_none.transpose() == nothing
    assert ok_some.transpose() == Option.Something(Result.Ok("meow"))
    assert err.transpose() == Option.Something(Result.Err("fuck"))


def test_flatten(ok, err):
    nesty = Result.Ok(ok)
    nesty2 = Result.Ok(err)

    assert nesty.flatten() == ok
    assert nesty2.flatten() == err
    assert err.flatten() == err
