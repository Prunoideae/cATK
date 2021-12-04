from typing import Any, Callable, Generic, Type, TypeVar, Union


def cached(fn):
    '''
    Cache an output of a certain fn,
    which means the subsequent call will be skipped and only initial result will be returned.
    '''
    r = None

    def inner(*args, **kwargs):
        nonlocal r
        if r is not None:
            return r
        r = fn(*args, **kwargs)
        return r

    return inner


T = TypeVar("T")


def cached_once(value: T):
    '''
    Cache the output once the output equals to `value`.
    '''
    f = False
    r = None

    def deco(fn):
        def inner(*args, **kwargs) -> T:
            nonlocal f, r, value
            if not f:
                f = (r := fn(*args, **kwargs)) == value
            return r
        return inner
    return deco


def oneshot(fn: Callable):
    '''
    Only run the decorated once, all subsequent call will
    be skipped and return none.
    '''
    f = False

    def inner(*args, **kwargs) -> T:
        nonlocal f
        if f:
            return None
        else:
            f = True
            return fn(*args, **kwargs)

    return inner


T = TypeVar("T")
TT = TypeVar("TT")


def singleton(*args, **kwargs) -> Union[T, TT]:
    '''
    Replace the current namespace with the instantiated one of the class,
    or simply the result of function if the decorated one is function.
    '''
    def inner(fn: Union[Callable[..., T], Type[TT]]):
        return fn(*args, **kwargs)
    return inner
