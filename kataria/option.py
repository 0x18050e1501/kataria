from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Generic, TypeVar

from kataria import Iterable
from kataria.common import Panic

if TYPE_CHECKING:
    from kataria.result import Result

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")
F = TypeVar("F")
R = TypeVar("R")


class Option(Generic[T], Iterable[T]):
    Item = T

    def __init__(self, is_some: bool, item: T):
        self._inner = item if is_some else None
        self._is_some = is_some

    def __eq__(self, other: "Option[T]"):
        if self.is_some() and other.is_some():
            return self.unwrap() == other.unwrap()
        else:
            return self.is_none() and other.is_none()

    def __repr__(self):
        if self._is_some:
            return f"Option.Some({repr(self._inner)})"
        return "Option.None"

    def __str__(self):
        if self._is_some:
            return f"Option.Some({str(self._inner)})"
        return "Option.None"

    def next(self) -> "Option[Item]":
        return self

    @classmethod
    def Something(cls, value) -> "Option[T]":
        return cls(True, value)

    @classmethod
    def Nothing(cls) -> "Option[T]":
        return cls(False, None)

    def is_some(self) -> bool:
        return self._is_some

    def is_some_and(self, op: Callable[[T], bool]) -> bool:
        return self.is_some() and op(self._inner)

    def is_none(self) -> bool:
        return not self._is_some

    def expect(self, e_msg: str) -> T:
        if self.is_none():
            raise Panic(e_msg)
        return self._inner

    def unwrap(self) -> T:
        if self.is_none():
            raise Panic
        return self._inner

    def unwrap_or(self, default: T) -> T:
        return self._inner if self.is_some() else default

    def unwrap_or_else(self, f: Callable[[], T]) -> T:
        return self._inner if self.is_some() else f()

    def map(self, op: Callable[[T], U]) -> "Option[U]":
        if self.is_some():
            self._inner = op(self._inner)

        return self

    def inspect(self, op: Callable[[T], None]) -> "Option[T]":
        if self.is_some():
            op(self._inner)
        return self

    def map_or(self, default: U, op: Callable[[T], U]) -> U:
        if self.is_some():
            return op(self._inner)
        else:
            return default

    def map_or_else(self, default: Callable[[], U], op: Callable[[T], U]) -> U:
        if self.is_some():
            return op(self._inner)
        else:
            return default()

    def ok_or(self, err: E) -> Result[T, E]:
        from kataria.result import Result

        if self.is_some():
            return Result.Ok(self._inner)
        else:
            return Result.Err(err)

    def ok_or_else(self, op: Callable[[], E]) -> Result[T, E]:
        from kataria.result import Result

        if self.is_some():
            return Result.Ok(self._inner)
        else:
            return Result.Err(op())

    def bool_and(self, other: "Option[T]") -> "Option[T]":
        if self.is_some():
            return other
        else:
            return self

    def and_then(self, op: Callable[[T], "Option[U]"]) -> "Option[U]":
        if self.is_none():
            return self
        else:
            return op(self._inner)

    def filter(self, predicate: Callable[[T], bool]) -> "Option[T]":
        if self.is_some() and predicate(self._inner):
            return self
        return Option.Nothing()

    def bool_or(self, optb: "Option[T]") -> "Option[T]":
        if self.is_some():
            return self
        return optb

    def or_else(self, op: Callable[[], "Option[T]"]) -> "Option[T]":
        if self.is_some():
            return self
        return op()

    def bool_xor(self, optb: "Option[T]") -> "Option[T]":
        if self.is_some() and optb.is_none():
            return self
        elif self.is_none() and optb.is_some():
            return optb
        else:
            return Option.Nothing()

    def replace(self, value: T) -> "Option[T]":
        old = self.__class__(self._is_some, self._inner)
        self._inner = value
        self._is_some = True
        return old

    def zip(self, other: "Option[U]") -> "Option[(T, U)]":
        if self.is_some() and other.is_some():
            return Option.Something((self._inner, other._inner))
        return Option.Nothing()

    def zip_with(self, other: "Option[U]", op: Callable[[T, U], R]) -> "Option[R]":
        if self.is_some() and other.is_some():
            return Option.Something(op(self._inner, other._inner))
        return Option.Nothing()

    def unzip(self: "Option[(T, U)]") -> ("Option[T]", "Option[U]"):
        if self.is_some():
            t, u = self._inner
            return Option.Something(t), Option.Something(u)
        return Option.Nothing(), Option.Nothing()

    def transpose(self: "Option[Result[T, E]]") -> "Result[Option[T], E]":
        from kataria.result import Result

        if self.is_some():
            if self._inner.is_ok():
                return Result.Ok(Option.Something(self._inner.unwrap()))
            return Result.Err(self._inner.unwrap_err())
        return Result.Ok(Option.Nothing())

    def flatten(self: "Option[Option[T]]") -> "Option[T]":
        if self.is_some():
            return self._inner
        return self
