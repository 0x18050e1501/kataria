from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Generic, TypeVar

from kataria.common import Panic
from kataria.iterable import Iterable

if TYPE_CHECKING:
    from kataria.option import Option

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")
F = TypeVar("F")


class Result(Generic[T, E], Iterable[T]):
    Item = T

    def __init__(self, is_ok: bool, value: T | E):
        self._is_ok = is_ok
        self._value = value

    def __eq__(self, other: "Result[T, E]"):
        if self.is_ok() and other.is_ok():
            return self.unwrap() == other.unwrap()
        elif self.is_err() and other.is_err():
            return self.unwrap_err() == other.unwrap_err()
        else:
            return False

    def __repr__(self):
        return f"Result.{'Ok' if self._is_ok else 'Err'}({repr(self._value)})"

    def __str__(self):
        return f"Result.{'Ok' if self._is_ok else 'Err'}({str(self._value)})"

    def next(self) -> "Option[T]":
        return self.ok()

    @classmethod
    def Ok(cls, value: T) -> "Result[T, E]":
        return cls(True, value)

    @classmethod
    def Err(cls, error: E) -> "Result[T, E]":
        return cls(False, error)

    def is_ok(self) -> bool:
        return self._is_ok

    def is_err(self) -> bool:
        return not self._is_ok

    def is_ok_and(self, op: Callable[[T], bool]) -> bool:
        return self.is_ok() and op(self._value)

    def is_err_and(self, op: Callable[[E], bool]) -> bool:
        return self.is_err() and op(self._value)

    def ok(self) -> Option[T]:
        from kataria.option import Option

        return Option(self.is_ok(), self._value)

    def err(self) -> Option[E]:
        from kataria.option import Option

        return Option(self.is_err(), self._value)

    def map(self, op: Callable[[T], U]) -> "Result[U, E]":
        if self.is_ok():
            try:
                self._value = op(self._value)
            except Exception as e:
                return self.Err(e)
        return self

    def map_or(self, default: U, op: Callable[[T], U]) -> U:
        if self.is_err():
            return default
        return op(self._value)

    def map_or_else(self, default: Callable[[E], U], op: Callable[[T], U]) -> U:
        if self.is_err():
            return default(self._value)
        return op(self._value)

    def map_err(self, op: Callable[[E], F]) -> "Result[T, F]":
        if self.is_err():
            self._value = op(self._value)
        return self

    def inspect(self, op: Callable[[T], None]) -> "Result[T, E]":
        if self.is_ok():
            op(self._value)
        return self

    def inspect_err(self, op: Callable[[E], None]) -> "Result[T, E]":
        if self.is_err():
            op(self._value)
        return self

    def expect(self, msg: str) -> T:
        if self.is_ok():
            return self._value
        raise Panic(self._value, msg)

    def unwrap(self) -> T:
        if self.is_ok():
            return self._value
        raise Panic(self._value)

    def expect_err(self, msg: str) -> E:
        if self.is_err():
            return self._value
        raise Panic(self._value, msg)

    def unwrap_err(self) -> E:
        if self.is_err():
            return self._value
        raise Panic(self._value)

    def bool_and(self, other: "Result[U, E]") -> "Result[U, E]":
        if self.is_ok():
            return other
        return self

    def and_then(self, op: Callable[[T], "Result[T, E]"]) -> "Result[T, E]":
        if self.is_err():
            return self

        return op(self._value)

    def bool_or(self, other: "Result[T, F]") -> "Result[T, F]":
        if self.is_ok():
            return self
        return other

    def or_else(self, op: Callable[[E], "Result[T, F]"]) -> "Result[T, F]":
        if self.is_err():
            return op(self._value)
        return self

    def unwrap_or(self, default: T) -> T:
        if self.is_ok():
            return self._value
        return default

    def unwrap_or_else(self, op: Callable[[E], T]) -> T:
        if self.is_ok():
            return self._value
        return op(self._value)

    def transpose(self: "Result[Option[T], E]") -> "Option[Result[T, E]]":
        from kataria.option import Option

        if self.is_ok():
            if self._value.is_none():
                return Option.Nothing()
            return Option.Something(Result.Ok(self._value.unwrap()))
        return Option.Something(Result.Err(self._value))

    def flatten(self: "Result[Result[T, E], E]") -> "Result[T, E]":
        if self.is_err():
            return self
        return self._value
