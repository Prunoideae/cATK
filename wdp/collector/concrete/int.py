from wdp.collector.concrete.common import ValueField


class Int(ValueField[int]):
    type = int

    def ranged(self, lower: int = None, upper: int = None):
        def validate(value: int):
            if (lower is not None and lower > value) or (upper is not None and upper < value):
                raise ValueError(f"Value {value} not in bound {(lower, upper)}.")
        return self.with_validator(validator=validate)

    def non(self, *numbers: int):
        def validate(value: int):
            if value in numbers:
                raise ValueError(f"Value {value} is in {numbers}, which is not allowed.")
        return self.with_validator(validator=validate)
