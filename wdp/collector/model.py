from abc import ABC, abstractclassmethod, abstractmethod
from typing import Generic, List, TypeVar

from wdp.util.error import UnsatisfiedError


class Default(ABC):

    @abstractclassmethod
    def default(cls): ...


class Resolveable(ABC):
    '''
    By implementing this, the class will be able to be instantiated as a field spec.
    '''
    @abstractmethod
    def resolve(self, k: str, namespace: "NameSpace"): ...


T = TypeVar("T")
I = TypeVar("I")


class Field(ABC, Generic[I]):

    @abstractmethod
    def accept(self: T, value) -> T: ...

    @abstractmethod
    def unwrap(self) -> I: ...

    def __call__(self, value) -> T:
        return self.accept(value)


class NameSpace():

    def __init__(self, inner: dict = {}) -> None:
        self.__dict__ |= inner

    def __getitem__(self, k: str):
        return self.__dict__[k]

    def merge(self, others: dict):
        self.__dict__ |= others

    def get(self, others: object):
        self.merge({k: v for k, v in others.__dict__.items() if isinstance(v, (Field, Resolveable,))})
        return self

    def paste(self, holder: object):
        '''
        Paste the content into the other object.

        No mutation or checking is occurred during this.
        '''
        unsatisfied = []
        for k, v in holder.__class__.__dict__.items():
            if isinstance(v, (Field, Resolveable)):
                if k in self.__dict__:
                    holder.__dict__[k] = self.__dict__[k]
                else:
                    unsatisfied.append(k)
        return unsatisfied

    def inject(self, holder: object) -> List[str]:
        '''
        Injects the content into the holder object.

        The holder object must only have one class.
        '''
        unsatisfied = []
        for k, v in holder.__class__.__dict__.items():
            if isinstance(v, Field):
                if k in self.__dict__:
                    holder.__dict__[k] = v.accept(self.__dict__[k])
                else:
                    unsatisfied.append(k)
            elif isinstance(v, Resolveable):
                try:
                    holder.__dict__[k] = v.resolve(k, self)
                except UnsatisfiedError as e:
                    unsatisfied += e.unsats

        return unsatisfied
