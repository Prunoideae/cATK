class UnsatisfiedError(Exception):
    '''
    The required names are not satisfied.
    '''

    def __init__(self, args) -> None:
        self.unsats = args


def throw_if_false(assertion: bool, error: Exception):
    if not assertion:
        raise error
