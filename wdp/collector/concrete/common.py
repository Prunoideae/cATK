from typing import Callable, List, Type, TypeVar
from wdp.collector.model import Field

T = TypeVar("T")
Self = TypeVar("Self")


class ValueField(Field[T]):
    type = None

    def __init__(self) -> None:
        super().__init__()
        self._validators: List[Callable[[T], None]] = []
        self._unwrapped = False

    def accept(self, value):
        '''
        Accepts a value of AnyType value, which can simply be casted by
        type constructor.

        This will modify the field instance itself, which sets the field 
        `inner` to parsed value.
        '''
        if isinstance(value, type(self)):
            return value

        value: T = self.type(value)
        for v in self._validators:
            v(value)
        self.inner: T = self.type(value)
        return self if not self._unwrapped else self.inner

    def unwrap(self) -> T:
        return self.inner

    def unwrapped(self) -> T:
        self._unwrapped = True
        return self

    def with_validator(self: Self, validator: Callable[[T], None]) -> Self:
        self._validators.append(validator)
        return self


class SimpleField(Field[T]):
    '''
    A simple wrapper for anytype, in case you don't want such a thing.

    This should be transparent, by which it means the accept will not return 
    the instance itself, but the casted value of the type it holds.
    '''

    def __init__(self, type: Type[T]) -> None:
        super().__init__()
        self.type = type

    def unwrap(self) -> T:
        raise NotImplementedError("This value is transparent.")

    def accept(self, value) -> T:
        return self.type(value)
