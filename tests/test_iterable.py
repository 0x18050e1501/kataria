import pytest

from kataria import NativeIterable, Option, Result, SequenceFromIterable
from kataria.common import State
from kataria.iterable import OptionSequenceIterable, StringFromIterable

from .fixtures import call_counted, finite_iter, infinite_iter


def test_count(finite_iter):
    assert finite_iter.count() == 10


def test_collect(finite_iter):
    expected = list(range(10))
    actual = finite_iter.collect(SequenceFromIterable())

    assert expected == actual


def test_last(finite_iter):
    assert finite_iter.last() == Option.Something(9)


def test_advance_by(finite_iter):
    assert finite_iter.advance_by(4) == Result.Ok(None)
    assert finite_iter.next() == Option.Something(4)

    # 3 steps remaining that were empty
    assert finite_iter.advance_by(8) == Result.Err(3)


def test_nth(finite_iter, infinite_iter):
    # nth is 0 indexed
    assert finite_iter.nth(4) == Option.Something(4)
    assert finite_iter.nth(7) == Option.Nothing()
    assert infinite_iter.nth(100) == Option.Something(100)
    assert infinite_iter.nth(100) == Option.Something(201)
    assert infinite_iter[100] == Option.Something(302)
    with pytest.raises(ValueError):
        _ = infinite_iter[-1]


def test_step_by(infinite_iter):
    assert infinite_iter.step_by(2).take(5).collect(SequenceFromIterable()) == [
        0,
        2,
        4,
        6,
        8,
    ]
    with pytest.raises(ValueError):
        _ = infinite_iter.step_by(0)


def test_chain(finite_iter, infinite_iter):
    it_res = finite_iter.chain(infinite_iter).take(15).collect(SequenceFromIterable())

    range_res = list(range(10))
    range_res.extend(range(5))

    assert it_res == range_res


def test_zip(finite_iter, infinite_iter):
    expected = [(i, i) for i in range(10)]
    actual = finite_iter.zip(infinite_iter).collect(SequenceFromIterable())

    assert expected == actual


def test_map(finite_iter):
    expected = [i * 2 for i in range(10)]
    actual = finite_iter.map(lambda v: v * 2).collect(SequenceFromIterable())

    assert expected == actual


def test_for_each(finite_iter, call_counted):
    finite_iter.for_each(call_counted)
    assert call_counted == 10


def test_filter(finite_iter):
    expected = [1, 3, 5, 7, 9]
    actual = finite_iter.filter(lambda v: v % 2 != 0).collect(SequenceFromIterable())

    assert expected == actual


def test_filter_map(finite_iter):
    def filt_map(item):
        if item % 2 == 0:
            return Option.Nothing()
        return Option.Something(item * 2)

    expected = [2, 6, 10, 14, 18]
    actual = finite_iter.filter_map(filt_map).collect(SequenceFromIterable())

    assert expected == actual


def test_enumerate(finite_iter):
    expected = list(enumerate(range(10)))
    actual = finite_iter.enumerate().collect(SequenceFromIterable())

    assert expected == actual


def test_peekable(finite_iter):
    it = finite_iter.peekable()

    assert it.peek() == Option.Something(0)

    it.advance_by(5)

    v = it.peek()
    assert it.peek() == v
    assert v == it.next()
    assert it.peek() == Option.Something(6)


def test_skip_while(finite_iter):
    expected = [7, 8, 9]
    actual = finite_iter.skip_while(lambda v: v < 7).collect(SequenceFromIterable())

    assert expected == actual


def test_take_while(finite_iter):
    expected = [0, 1, 2, 3, 4]
    actual = finite_iter.take_while(lambda v: v < 5).collect(SequenceFromIterable())

    assert expected == actual


def test_map_while(infinite_iter):
    def map_while(item):
        if item < 5:
            return Option.Something(item**2)
        return Option.Nothing()

    expected = [0, 1, 4, 9, 16]
    actual = infinite_iter.map_while(map_while).collect(SequenceFromIterable())

    assert expected == actual


def test_skip(finite_iter):
    expected = list(range(5, 10))
    actual = finite_iter.skip(5).collect(SequenceFromIterable())

    assert expected == actual


def test_take(infinite_iter):
    expected = list(range(20))
    actual = infinite_iter.take(20).collect(SequenceFromIterable())

    assert expected == actual


def test_scan():
    def scanner(state: State, item):
        state.change(lambda v: v * item)

        if state.get() > 6:
            return Option.Nothing()

        return Option.Something(-state.get())

    it = NativeIterable([1, 2, 3, 4]).scan(1, scanner)

    assert it.next() == Option.Something(-1)
    assert it.next() == Option.Something(-2)
    assert it.next() == Option.Something(-6)
    assert it.next() == Option.Nothing()


def test_flat_map():
    words = ["alpha", "beta", "gamma"]

    merged = (
        NativeIterable(words)
        .flat_map(lambda w: NativeIterable(w))
        .collect(StringFromIterable())
    )

    assert merged == "alphabetagamma"


def test_flatten():
    it1 = NativeIterable(range(4))
    it2 = NativeIterable(range(3))

    expected = [0, 1, 2, 3, 0, 1, 2]
    actual = NativeIterable((it1, it2)).flatten().collect(SequenceFromIterable())

    assert expected == actual


def test_fuse():
    expected = list(range(5))

    first = (
        NativeIterable(range(5))
        .map(lambda v: Option.Something(v))
        .collect(SequenceFromIterable())
    )

    second = (
        NativeIterable(range(10, 15))
        .map(lambda v: Option.Something(v))
        .collect(SequenceFromIterable())
    )

    test_iter = OptionSequenceIterable(first + [Option.Nothing()] + second)

    actual = test_iter.fuse().collect(SequenceFromIterable())

    assert expected == actual


def test_inspect(finite_iter, call_counted):
    expected = list(range(10))
    actual = finite_iter.inspect(call_counted).collect(SequenceFromIterable())

    assert expected == actual
    assert call_counted == 10


def test_partition(finite_iter):
    expected_a = [0, 2, 4, 6, 8]
    expected_b = [1, 3, 5, 7, 9]

    actual_a, actual_b = finite_iter.partition(
        lambda v: v % 2 == 0, SequenceFromIterable(), SequenceFromIterable()
    )

    assert expected_a == actual_a
    assert expected_b == actual_b


def test_fold(finite_iter):
    expected = sum(range(10)) + 24
    actual = finite_iter.fold(24, lambda u, t: u + t)

    assert expected == actual


def test_reduce(finite_iter):
    expected = 45
    actual = finite_iter.reduce(lambda a, b: a + b)

    assert expected == actual


def test_all(finite_iter, infinite_iter, call_counted):
    assert finite_iter.all(lambda t: t >= 0)
    assert not infinite_iter.inspect(call_counted).all(lambda t: t < 5)
    assert call_counted == 6


def test_any(finite_iter, infinite_iter, call_counted):
    assert finite_iter.inspect(call_counted).any(lambda t: t == 4)
    assert call_counted == 5


def test_find(finite_iter, infinite_iter):
    def waldo(item):
        return item == 42

    assert finite_iter.find(waldo) == Option.Nothing()
    assert infinite_iter.find(waldo) == Option.Something(42)
    # note: if waldo isn't found on an infinite iterator, this blocks forever.


def test_find_map(finite_iter, infinite_iter):
    def waldo(item):
        if item == 42:
            return Option.Something("the answer")
        return Option.Nothing()

    assert finite_iter.find_map(waldo) == Option.Nothing()
    assert infinite_iter.find_map(waldo) == Option.Something("the answer")


def test_position(finite_iter, infinite_iter):
    def waldo(item):
        return item == 42

    assert finite_iter.position(waldo) == Option.Nothing()
    assert infinite_iter.position(waldo) == Option.Something(42)


def test_cycle(finite_iter):
    expected = list(range(10)) * 3
    actual = finite_iter.cycle().take(30).collect(SequenceFromIterable())

    assert expected == actual
