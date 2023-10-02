from abc import ABC
from typing import (
    TYPE_CHECKING,
    Callable,
    Container,
    Generic,
    MutableMapping,
    MutableSequence,
    MutableSet,
    TypeVar,
)

from kataria.common import State

if TYPE_CHECKING:
    from kataria.option import Option
    from kataria.result import Result

T = TypeVar("T")
U = TypeVar("U")
St = TypeVar("St", bound=State)
StV = TypeVar("StV")
C = TypeVar("C", bound=Container)
K = TypeVar("K")
V = TypeVar("V")


class FromIterable(Generic[C, T], ABC):
    def __init__(self, collection: C):
        self.collection = collection

    def add(self, item: T):
        return NotImplemented

    def finish(self) -> C:
        return self.collection


class SequenceFromIterable(FromIterable[MutableSequence[T], T]):
    def __init__(self):
        super().__init__(list())

    @classmethod
    def from_existing(cls, lst: MutableSequence[T]):
        return super().__init__(lst)

    def add(self, item: T):
        self.collection.append(item)


class StringFromIterable(FromIterable[str, str]):
    def __init__(self):
        super().__init__("")

    @classmethod
    def from_existing(cls, s: str):
        return super().__init__(s)

    def add(self, item: str):
        self.collection += item


class MappingFromIterable(FromIterable[MutableMapping[K, V], (K, V)]):
    def __init__(self):
        super().__init__(dict())

    @classmethod
    def from_existing(cls, mapping: MutableMapping):
        return super().__init__(mapping)

    def add(self, item: (K, V)):
        k, v = item
        self.collection[k] = v


class SetFromIterable(FromIterable[MutableSet[T], T]):
    def __init__(self):
        super().__init__(set())

    @classmethod
    def from_existing(cls, st: MutableSet[T]):
        return super().__init__(st)

    def add(self, item: T):
        self.collection.add(item)


class Iterable(Generic[T], ABC):
    Item = T

    def next(self) -> "Option[Item]":
        return NotImplemented

    def __iter__(self):
        return self

    def __next__(self):
        item = self.next()
        if item.is_some():
            return item.unwrap()
        raise StopIteration

    def __getitem__(self, item: int) -> "Option[Item]":
        if item < 0:
            raise ValueError("iterators cannot be accessed in reverse")
        return self.nth(item)

    def count(self) -> int:
        i = 0
        while self.next().is_some():
            i += 1
        return i

    def last(self) -> "Option[Item]":
        prv = self.next()
        if prv.is_some():
            while True:
                nxt = self.next()
                if nxt.is_none():
                    break
                prv = nxt

        return prv

    def advance_by(self, n: int) -> "Result[None, int]":
        from kataria.result import Result

        for steps_remaining in range(n, 0, -1):
            item = self.next()
            if item.is_none():
                return Result.Err(steps_remaining)

        return Result.Ok(None)

    def nth(self, n: int) -> "Option[Item]":
        item = self.next()
        for _ in range(n):
            item = self.next()

        return item

    def step_by(self, step: int) -> "StepBy[Item]":
        return StepBy(step, self)

    def chain(self, other: "Iterable[Item]") -> "Chain[Item]":
        return Chain(self, other)

    def zip(self, other: "Iterable") -> "Zip[(T, U)]":
        return Zip(self, other)

    def map(self, op: Callable[[T], U]) -> "Map[U]":
        return Map(op, self)

    def for_each(self, op: Callable[[Item], None]) -> None:
        while (item := self.next()).is_some():
            op(item.unwrap())

    def filter(self, predicate: Callable[[Item], bool]) -> "Filter[Item]":
        return Filter(predicate, self)

    def filter_map(self, filter_map: Callable[[T], "Option[U]"]) -> "FilterMap[U]":
        return FilterMap(filter_map, self)

    def enumerate(self) -> "Enumerate[(int, Item)]":
        return Enumerate(self)

    def peekable(self) -> "Peekable[Item]":
        return Peekable(self)

    def skip_while(self, predicate: Callable[[Item], bool]) -> "SkipWhile[Item]":
        return SkipWhile(predicate, self)

    def take_while(self, predicate: Callable[[Item], bool]) -> "TakeWhile[Item]":
        return TakeWhile(predicate, self)

    def map_while(self, predicate: Callable[[T], "Option[U]"]) -> "MapWhile[U]":
        return MapWhile(predicate, self)

    def skip(self, n: int) -> "Skip[Item]":
        return Skip(n, self)

    def take(self, n: int) -> "Take[Item]":
        return Take(n, self)

    # curse python's nonexplicit mutability
    def scan(self, initial_state: StV, op: Callable[[St, T], "Option[U]"]) -> "Scan[U]":
        return Scan(initial_state, op, self)

    def flat_map(self, op: Callable[[T], U]) -> "FlatMap[U]":
        return FlatMap(op, self)

    def flatten(self) -> "Flatten[Item]":
        return Flatten(self)

    def fuse(self) -> "Fuse[Item]":
        return Fuse(self)

    def inspect(self, op: Callable[[Item], None]) -> "Inspect[Item]":
        return Inspect(op, self)

    def collect(self, into: "FromIterable[C]") -> C:
        for item in self:
            into.add(item)
        return into.finish()

    def partition(
        self,
        predicate: Callable[[Item], bool],
        a: "FromIterable[C]",
        b: "FromIterable[C]",
    ) -> ("FromIterable[C]", "FromIterable[C]"):
        for item in self:
            if predicate(item):
                a.add(item)
            else:
                b.add(item)

        return a.finish(), b.finish()

    def fold(self, init: U, op: Callable[[U, Item], U]) -> U:
        res = init
        for item in self:
            res = op(res, item)
        return res

    def reduce(self, op: Callable[[Item, Item], Item]) -> "Option[Item]":
        if (a := self.next()).is_some():
            a = a.unwrap()
            for b in self:
                a = op(a, b)
        return a

    def all(self, predicate: Callable[[Item], bool]) -> bool:
        return all(self.map(predicate))

    def any(self, predicate: Callable[[Item], bool]) -> bool:
        return any(self.map(predicate))

    def find(self, predicate: Callable[[Item], bool]) -> "Option[Item]":
        from kataria.option import Option

        while (item := self.next()).is_some():
            if predicate(item.unwrap()):
                return item
        return Option.Nothing()

    def find_map(self, predicate: Callable[[Item], "Option[U]"]) -> "Option[U]":
        from kataria.option import Option

        while (item := self.next()).is_some():
            if (mapped := predicate(item.unwrap())).is_some():
                return mapped

        return Option.Nothing()

    def position(self, predicate: Callable[[Item], bool]) -> "Option[int]":
        from kataria.option import Option

        i = 0
        for item in self:
            if predicate(item):
                return Option.Something(i)
            i += 1

        return Option.Nothing()

    def cycle(self) -> "Cycle[Item]":
        return Cycle(self)


class NativeIterable(Iterable[T]):
    Item = T

    def __init__(self, it):
        self._inner = iter(it)

    def next(self) -> "Option[Item]":
        from kataria.option import Option

        try:
            item = self._inner.__next__()
            return Option.Something(item)
        except StopIteration:
            return Option.Nothing()


class OptionSequenceIterable(NativeIterable):
    Item = T

    def next(self) -> "Option[Item]":
        from kataria.option import Option

        try:
            return self._inner.__next__()
        except StopIteration:
            return Option.Nothing()


class StepBy(Iterable):
    Item = Iterable.Item

    def __init__(self, step: int, inner: Iterable):
        if step < 1:
            raise ValueError("step has to be positive")
        self._step = step
        self._inner = inner

    def next(self) -> "Option[Item]":
        out = self._inner.next()
        for _ in range(self._step - 1):
            self._inner.next()

        return out


class Chain(Iterable):
    Item = Iterable.Item

    def __init__(self, a: Iterable[Item], b: Iterable[Item]):
        self._a = a
        self._b = b

    def next(self) -> "Option[Item]":
        a_item = self._a.next()
        if a_item.is_some():
            return a_item
        return self._b.next()


class Zip(Iterable):
    Item = (T, U)

    def __init__(self, a: Iterable[T], b: Iterable[U]):
        self._a = a
        self._b = b

    def next(self) -> "Option[Item]":
        from kataria.option import Option

        a_item = self._a.next()
        b_item = self._b.next()
        if a_item.is_some() and b_item.is_some():
            return Option.Something((a_item.unwrap(), b_item.unwrap()))
        return Option.Nothing()


class Map(Iterable):
    Item = U

    def __init__(self, mapper: Callable[[T], Item], inner: Iterable[T]):
        self._i = inner
        self._op = mapper

    def next(self) -> "Option[Item]":
        return self._i.next().map(self._op)


class Filter(Iterable):
    Item = Iterable.Item

    def __init__(self, predicate: Callable[[Item], bool], inner: Iterable[Item]):
        self._pred = predicate
        self._i = inner

    def next(self) -> "Option[Item]":
        from kataria.option import Option

        while (item := self._i.next()).is_some():
            if self._pred(item.unwrap()):
                return item
        return Option.Nothing()


class FilterMap(Iterable):
    Item = U

    def __init__(self, filter_map: Callable[[T], "Option[Item]"], inner: Iterable[T]):
        self._op = filter_map
        self._i = inner

    def next(self) -> "Option[Item]":
        from kataria.option import Option

        while (item := self._i.next()).is_some():
            if (mapped := self._op(item.unwrap())).is_some():
                return mapped

        return Option.Nothing()


class Enumerate(Iterable):
    Item = Iterable.Item

    def __init__(self, inner: Iterable[Item]):
        self._inner = inner
        self._count = 0

    def next(self) -> "Option[(int, Item)]":
        self._count += 1
        return self._inner.next().map(lambda i: (self._count - 1, i))


class Peekable(Iterable):
    Item = Iterable.Item

    def __init__(self, inner: Iterable[Item]):
        self._inner = inner
        self._cache = self._inner.next()

    def next(self) -> "Option[Item]":
        out = self._cache
        self._cache = self._inner.next()
        return out

    def peek(self) -> "Option[Item]":
        return self._cache


class SkipWhile(Iterable):
    Item = Iterable.Item

    def __init__(self, predicate: Callable[[Item], bool], inner: Iterable[Item]):
        self._inner = inner
        self._pred = predicate
        self._done = False

    def next(self) -> "Option[Item]":
        if self._done:
            return self._inner.next()

        while (item := self._inner.next()).is_some():
            if self._pred(item.unwrap()):
                continue
            self._done = True
            break
        return item


class TakeWhile(Iterable):
    Item = Iterable.Item

    def __init__(self, predicate: Callable[[Item], bool], inner: Iterable[Item]):
        self._inner = inner
        self._pred = predicate
        self._done = False

    def next(self) -> "Option[Item]":
        from kataria.option import Option

        if self._done:
            return Option.Nothing()

        item = self._inner.next()
        if item.is_some_and(self._pred):
            return item

        self._done = True
        return Option.Nothing()


class MapWhile(Iterable):
    Item = U

    def __init__(self, predicate: Callable[[T], "Option[Item]"], inner: Iterable[T]):
        self._inner = inner
        self._pred = predicate
        self._done = False

    def next(self) -> "Option[Item]":
        from kataria.option import Option

        if self._done:
            return Option.Nothing()

        if (item := self._inner.next().and_then(self._pred)).is_some():
            return item

        self._done = True
        return Option.Nothing()


class Skip(Iterable):
    Item = Iterable.Item

    def __init__(self, n: int, inner: Iterable[Item]):
        self._inner = inner

        for _ in range(n):
            self._inner.next()

    def next(self) -> "Option[Item]":
        return self._inner.next()


class Take(Iterable):
    Item = Iterable.Item

    def __init__(self, n: int, inner: Iterable[Item]):
        self._inner = inner
        self._remaining = n

    def next(self) -> "Option[Item]":
        from kataria.option import Option

        if self._remaining <= 0:
            return Option.Nothing()

        self._remaining -= 1

        return self._inner.next()


class Scan(Iterable):
    Item = U

    def __init__(
        self,
        initial_state: StV,
        op: Callable[[St, T], "Option[Item]"],
        inner: Iterable[T],
    ):
        self._inner = inner
        self._op = op
        self._state = State(initial_state)

    def next(self) -> "Option[Item]":
        from kataria.option import Option

        if (a := self._inner.next()).is_some():
            return self._op(self._state, a.unwrap())
        return Option.Nothing()


class FlatMap(Iterable):
    Item = U

    def __init__(self, op: Callable[[T], Iterable[Item]], inner: Iterable[T]):
        self._inner = inner
        self._op = op
        self._current = self._inner.next().map(self._op)

    def next(self) -> "Option[Item]":
        from kataria.option import Option

        if self._current.is_none():
            return Option.Nothing()

        if (item := self._current.unwrap().next()).is_some():
            return item
        else:
            self._current = self._inner.next().map(self._op)
            return self.next()


class Flatten(Iterable):
    Item = Iterable.Item

    def __init__(self, inner: Iterable[Iterable[Item]]):
        self._inner = inner
        self._current = self._inner.next()

    def next(self) -> "Option[Item]":
        from kataria.option import Option

        if self._current.is_none():
            return Option.Nothing()

        if (item := self._current.unwrap().next()).is_some():
            return item
        else:
            self._current = self._inner.next()
            return self.next()


class Fuse(Iterable):
    Item = Iterable.Item

    def __init__(self, inner: Iterable[Item]):
        self._inner = inner
        self._fused = False

    def next(self) -> "Option[Item]":
        from kataria.option import Option

        if self._fused:
            return Option.Nothing()

        if (item := self._inner.next()).is_none():
            self._fused = True
        return item


class Inspect(Iterable):
    Item = Iterable.Item

    def __init__(self, op: Callable[[Item], None], inner: Iterable[Item]):
        self._inner = inner
        self._op = op

    def next(self) -> "Option[Item]":
        return self._inner.next().inspect(self._op)


class Cycle(Iterable):
    Item = Iterable.Item

    def __init__(self, inner: Iterable[Item]):
        self._inner = inner
        self._buf = list()
        self._i = 0
        self._looping = False

    def next(self) -> "Option[Item]":
        from kataria.option import Option

        if self._looping:
            ret = Option.Something(self._buf[self._i])
            self._i = (self._i + 1) % len(self._buf)
            return ret

        if (item := self._inner.next()).is_some():
            self._buf.append(item.unwrap())
            return item

        self._looping = True
        return self.next()
