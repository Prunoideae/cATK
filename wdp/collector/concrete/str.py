import os
from .common import ValueField
from os import path


class Str(ValueField[str]):
    type = str


class FileLike(Str):
    def __init__(self, exists=True) -> None:
        self.exists = exists
        super().__init__()

    def accept(self, value):
        if self.exists and not path.isfile(value):
            raise ValueError(f"\"{value}\" is not a valid file.")
        return super().accept(value)


class DirLike(Str):
    def __init__(self, exists=True) -> None:
        self.exists = exists
        super().__init__()

    def accept(self, value):
        if self.exists and not path.isdir(value):
            raise ValueError(f"\"{value}\" is not a valid directory")
        return super().accept(value)

    def make(self):
        os.makedirs(self.inner, exist_ok=True)
