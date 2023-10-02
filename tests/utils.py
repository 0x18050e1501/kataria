from functools import total_ordering

from kataria import Panic


@total_ordering
class CallCounted:
    def __init__(self, func):
        self.f = func
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1
        return self.f(*args, **kwargs)

    def __eq__(self, other):
        return self.count == other

    def __lt__(self, other):
        return self.count < other

    def __repr__(self):
        return f"CallCounted({self.count})"


def assert_not_called():
    raise Panic
