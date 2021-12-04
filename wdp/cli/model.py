from abc import abstractclassmethod, abstractmethod
from typing import Any, List, Type, TypeVar, Union
from wdp.collector.concrete.common import SimpleField
from wdp.collector.model import Default, Field, NameSpace, Resolveable
from dataclasses import dataclass
from argparse import _ArgumentGroup, ArgumentParser, RawTextHelpFormatter

from wdp.runner.model import Runnable
from wdp.util.error import UnsatisfiedError

T = TypeVar("T")
I = TypeVar("I")


class ArgSpec(Field[T]):
    def __init__(self, arg: "Arg", field: Union[Field[T], Type[T]]) -> None:
        self.field = field if isinstance(field, Field) else SimpleField(field)
        self.arg = arg

    def inner(self) -> "Arg":
        return self.arg

    def accept(self: T, value) -> T:
        return self.field.accept(value)

    def unwrap(self) -> I:
        raise NotImplementedError("This value is transparent.")

    def assemble(self, name: str, group: Union[_ArgumentGroup, ArgumentParser]):
        inner = self.arg
        args = []
        if inner.short is not None:
            args.append(f"-{inner.short}")
        if inner.long is not None:
            args.append(f'--{inner.long}')
        if not args:
            args.append(f"--{name}")

        kwds = {}
        kwds['type'] = self.field
        kwds['required'] = inner.required
        if inner.default is not None:
            kwds['default'] = inner.default
        if inner.meta is not None:
            kwds['metavar'] = f"<{inner.meta}>"
        if inner.choices is not None:
            kwds['choices'] = inner.choices
        if inner.help is not None:
            kwds['help'] = inner.help
            if inner.default is not None:
                kwds['help'] += f" [{inner.default}]"

        if type(inner.default) is bool:
            group.add_argument(*args, action='store_false' if inner.default else 'store_true', help=inner.help)
        else:
            group.add_argument(*args, **kwds)


@dataclass
class Arg():
    '''
    A transparent layer of Field.

    Accepts a field instance by calling after the arg specification,
    and ONLY by this the arg is exposed to the CLI.
    '''

    required: bool = False
    help: str = None
    choices: List = None
    meta: str = None
    default: Any = None
    short: str = None
    long: str = None

    def field(self, field: Union[I, Type[I]]) -> I:
        return ArgSpec(self, field)


class ArgGroup(Resolveable):
    '''
    A group of arguments. Represents an arggroup in argparse.
    '''

    name = None

    def __init__(self) -> None:
        super().__init__()

    def resolve(self, k: str, namespace: "NameSpace"):
        unsat = namespace.inject(self)
        if unsat:
            raise UnsatisfiedError(unsat)
        return self

    def assemble(self) -> ArgumentParser:
        parser = ArgumentParser(add_help=False, formatter_class=RawTextHelpFormatter)
        group = parser.add_argument_group(self.name)
        for k, v in filter(lambda v: isinstance(v[1], ArgSpec), self.__class__.__dict__.items()):
            k: str
            v: ArgSpec
            v.assemble(k, group)
        return parser


class Command():
    '''
    Holder class for a specific command.
    '''

    def __init__(self, wrapped: Type[Runnable], name=None, help=None) -> None:
        self.wrapped = wrapped
        self.name = name
        self.help = help

    def assemble(self, to_attach: ArgumentParser) -> ArgumentParser:
        for k, v in self.wrapped.__dict__.items():
            if isinstance(v, ArgSpec):
                v.assemble(k, to_attach)
        return to_attach
