from abc import ABC, abstractmethod
from typing import Union
from wdp.util.formatter import MultiLine
from wdp.util.predicate import Predicate


class Explainable(ABC):

    '''
    By implementing this, the class can now explain their plan without 
    starting the actual task.
    '''

    @abstractmethod
    async def explain(self): ...


class Conditional(ABC):

    '''
    By implementing this, the class will be able to check if a given 
    condition is valid for the task to run.

    ...And when this assertion failed, the task will emit why.
    '''

    @abstractmethod
    def predicate(self) -> Union[Predicate, bool]: ...

    @abstractmethod
    def emit_error(self) -> MultiLine: ...


class Runnable(ABC):

    '''
    An async runner for a certain task.
    '''

    @abstractmethod
    async def run(self):
        pass
