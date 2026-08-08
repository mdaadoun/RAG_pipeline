"""Exponential backoff decorator wrapper adapted from shared workspace utilities."""

import time
from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def retry_with_backoff(
    retries: int = 3,
    backoff_factor: float = 1.5,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorator performing exponential backoff retry on transient failure."""

    def decorator(func: F) -> F:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            delay = 1.0
            while attempt < retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as err:
                    attempt += 1
                    if attempt >= retries:
                        raise err
                    time.sleep(delay)
                    delay *= backoff_factor

        return wrapper  # type: ignore[return-value]

    return decorator
