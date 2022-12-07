from typing import Callable


def all_args_not_none(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        if any([arg is None for arg in args] + [v is None for k, v in kwargs.items()]):
            raise ValueError(
                f"Found not defined args {args}. "
                f"Not defined kwargs {[(k, v) for k, v in kwargs.items() if v is None]}"
            )
        return func(*args, **kwargs)

    return wrapper
