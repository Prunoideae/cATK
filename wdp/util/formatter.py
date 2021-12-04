import sys
from .decorator import singleton
from typing import Union
from enum import Enum


class ColorEnum(Enum):
    DEFAULT = 0
    BOLD = 1
    NO_BOLD = 22
    UNDERLINE = 4
    NO_UNDERLINE = 24
    NEGATIVE = 7
    POSITIVE = 27
    FOREGROUND_BLACK = 30
    FOREGROUND_RED = 31
    FOREGROUND_GREEN = 32
    FOREGROUND_YELLOW = 33
    FOREGROUND_BLUE = 34
    FOREGROUND_MAGENTA = 35
    FOREGROUND_CYAN = 36
    FOREGROUND_WHITE = 37
    FOREGROUND_EXTENDED = 38
    FOREGROUND_DEFAULT = 39
    BACKGROUND_BLACK = 40
    BACKGROUND_RED = 41
    BACKGROUND_GREEN = 42
    BACKGROUND_YELLOW = 43
    BACKGROUND_BLUE = 44
    BACKGROUND_MAGENTA = 45
    BACKGROUND_CYAN = 46
    BACKGROUND_WHITE = 47
    BACKGROUND_EXTENDED = 48
    BACKGROUND_DEFAULT = 49
    BRIGHT_FOREGROUND_BLACK = 90
    BRIGHT_FOREGROUND_RED = 91
    BRIGHT_FOREGROUND_GREEN = 92
    BRIGHT_FOREGROUND_YELLOW = 93
    BRIGHT_FOREGROUND_BLUE = 94
    BRIGHT_FOREGROUND_MAGENTA = 95
    BRIGHT_FOREGROUND_CYAN = 96
    BRIGHT_FOREGROUND_WHITE = 97
    BRIGHT_BACKGROUND_BLACK = 100
    BRIGHT_BACKGROUND_RED = 101
    BRIGHT_BACKGROUND_GREEN = 102
    BRIGHT_BACKGROUND_YELLOW = 103
    BRIGHT_BACKGROUND_BLUE = 104
    BRIGHT_BACKGROUND_MAGENTA = 105
    BRIGHT_BACKGROUND_CYAN = 106
    BRIGHT_BACKGROUND_WHITE = 107


__formater_text__ = "\x1b[{}m" if sys.platform == "win32" else "\033[{}m"


@singleton()
class FormatterController():
    color_enabled = True
    single_ident = 4
    max_ident = 5


class Component():
    '''
    A text group consisting of a set of modifiers and a string.
    '''

    def __init__(self, text: str, *modifiers: ColorEnum) -> None:
        self.modifiers = list(modifiers)
        if not self.modifiers:
            self.modifiers = self.modifiers + [ColorEnum.DEFAULT]
        self.text = text

    def append(self, modifier: ColorEnum):
        self.modifiers.append(modifier)

    def format(self) -> str:
        if FormatterController.color_enabled:
            return "".join(__formater_text__.format(x.value) for x in self.modifiers) + self.text + __formater_text__.format(0)
        else:
            return self.text

    def __str__(self) -> str:
        return self.format()


class Line():
    '''
    A line of text consisting of multiple components.
    '''

    def __init__(self, *components: Component, sep: str = "") -> None:
        self.components = list(components)
        self.sep = sep

    def format(self) -> str:
        return self.sep.join(x.format() for x in self.components)

    def append(self, *components):
        self.components = self.components + list(components)

    def __str__(self) -> str:
        return self.format()


class NamedLine(Line):
    '''
    A line of text consisting of multiple components, while each component is assigned to a unique namespace.
    '''

    def __init__(self, sep: str = "", **components: Component) -> None:
        self.components = components
        self.sep = sep

    def remove(self, key: str):
        self.components.pop(key)

    def __getitem__(self, item: str):
        self.components.__getitem__(item)

    def __setitem__(self, item: str, value: Component):
        self.components.__setitem__(item, value)

    def format(self) -> str:
        return self.sep.join(x.format() for x in self.components.values())


class IdentedLine():
    '''
    A line with indentation.
    '''

    def __init__(self, line: Line, ident: int = 0, char=" ") -> None:
        self.line = line
        self.ident = ident
        self.char = char

    def add(self, ident):
        self.ident = self.ident + ident

    def sub(self, ident):
        self.ident = max(self.ident - ident, 0)

    def with_ident(self, ident) -> 'IdentedLine':
        return IdentedLine(self.line, ident=ident, char=self.char)

    def format(self) -> str:
        return self.char * min(self.ident, FormatterController.max_ident) * FormatterController.single_ident + self.line.format()

    def __str__(self) -> str:
        return self.format()


Blank = Line()


class MultiLine():
    '''
    Multiple lines with corresponding indentations.
    '''

    def __init__(self, *lines: Union[Line, IdentedLine, 'MultiLine'], ident: int = 0, char=" ") -> None:
        self.lines = [x if not isinstance(x, Line) else IdentedLine(x, ident=ident, char=char) for x in lines]
        self.ident = ident
        self.char = char

    def with_ident(self, ident) -> 'MultiLine':
        ident_lines = [x.with_ident(x.ident + ident - self.ident) for x in self.lines]
        return MultiLine(*ident_lines, ident=ident, char=self.char)

    def append(self, element: Union[Line, IdentedLine, 'MultiLine']):
        if isinstance(element, Line):
            element = IdentedLine(element)
        self.lines.append(element)

    def format(self) -> str:
        return "\n".join(x.format() for x in self.lines)

    def __str__(self) -> str:
        return self.format()


class NamedMultiLine(MultiLine):
    '''
    Multiple lines with corresponding indentations, while each component is assigned to a unique namespace.

    By default, the key should be `str`, but this can be changed if the entire components are built ontop
    other key types. But in any case, it's not good to have multiple key types.
    '''

    def __init__(self, ident: int = 0, char: str = "", **components: Union[Line, IdentedLine, MultiLine]) -> None:
        self.ident = ident
        self.char = char
        self.components = {k: v if not isinstance(v, Line) else IdentedLine(v, ident=ident, char=char) for k, v in components.items()}

    def remove(self, key: str):
        return self.components.pop(key)

    def append(self, key: str, element: Union[Line, IdentedLine, 'MultiLine']):
        self.components.__setitem__(key, element)

    def __getitem__(self, item: str):
        self.components.__getitem__(item)

    def __setitem__(self, item: str, value: Union[IdentedLine, MultiLine]):
        self.components.__setitem__(item, value)

    def with_ident(self, ident) -> 'MultiLine':
        components = {k: v.with_ident(v.ident + ident - self.ident) for k, v in self.components.items()}
        return NamedMultiLine(ident=ident, char=self.char, **components)
