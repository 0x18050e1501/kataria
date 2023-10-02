from typing import Callable, Generic, TypeVar


class Panic(Exception):
    ...


StV = TypeVar("StV")


class State(Generic[StV]):
    def __init__(self, val: StV):
        self.val = val

    def get(self) -> StV:
        return self.val

    def change(self, func: Callable[[StV], StV]) -> StV:
        new = func(self.get())
        return self.set(new)

    def set(self, v: StV) -> StV:
        old = self.get()
        self.val = v
        return old
