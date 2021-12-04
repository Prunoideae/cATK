import sys
from wdp.collector.model import NameSpace
from wdp.cli.model import ArgGroup, Command
from argparse import ArgumentParser, RawTextHelpFormatter
from typing import Dict

from wdp.runner.model import Runnable


__registry__: Dict[str, Command] = {}
__main__ = None


def command(name, help=None):
    '''
    A wrapper to markup certain class as a command.
    '''
    def inner(cls: object):
        nonlocal help
        if help is None:
            help = cls.__doc__
        if help:
            help = help.strip().replace("    ", "")
        cmd = Command(cls, name, help)
        global __registry__
        __registry__[name] = cmd
        return cls
    return inner


def inject_safe(namespace: NameSpace, inst):
    import sys
    try:
        unsat = namespace.inject(inst)
        if not unsat:
            return
        print(f"Missing keys {unsat}, which are not required, but have no default values.")
    except TypeError as t:
        print(str(t))
    sys.exit()


def main(program: str, command: Command) -> Runnable:
    '''
    Use a certain command as main entry of program, and run them
    '''
    parents = [x.assemble() for x in command.wrapped.__dict__.values() if isinstance(x, ArgGroup)]
    parser = ArgumentParser(prog=program, description=command.help, formatter_class=RawTextHelpFormatter, parents=parents)
    command.assemble(parser)
    namespace = NameSpace(vars(parser.parse_args()))

    inst = command.wrapped()
    inject_safe(namespace, inst)
    return inst


def commands(program: str, help: str) -> Runnable:
    '''
    Use the registered commands as subentries of program, and run them
    '''
    parser = ArgumentParser(prog=program, description=help, formatter_class=RawTextHelpFormatter)
    subs = parser.add_subparsers(dest="!command")
    for k, v in __registry__.items():
        parents = [x.assemble() for x in v.wrapped.__dict__.values() if isinstance(x, ArgGroup)]
        sub = subs.add_parser(v.name, parents=parents, help=v.help)
        v.assemble(sub)

    parsed_args = vars(parser.parse_args())
    command_dest = parsed_args.pop("!command")
    if command_dest is None:
        parser.print_help()
        sys.exit()
    inst = __registry__[command_dest].wrapped()
    inject_safe(NameSpace({k: v for k, v in parsed_args.items() if v is not None}), inst)
    return inst
