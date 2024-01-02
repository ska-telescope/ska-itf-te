"""Utility methods for working with TMC leafnodes."""
from __future__ import annotations

import logging
import time
from typing import Any, Callable, ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")

logger = logging.getLogger(__name__)

_listener: None | Listener = None


def get_listener() -> Listener:
    """
    Retrieve the global Listener.

    :return: The global Listener.
    :rtype: Listener
    """
    global _listener
    _listener = Listener() if _listener is None else _listener
    return _listener


class Listener:
    """Listener is used to record retries."""

    def __init__(self) -> None:
        """Initialise the listener."""
        self.messages: list[str] = []

    def record(self, message: str):
        """
        Record the message sent to the listener.

        :param message: The message.
        :type message: str
        """
        self.messages.append(message)


def retry(nr_of_reties: int = 3, wait_time: float = 1) -> Any:
    """
    Create a wrapper method which can be used to retry a command until it succeeds.

    :param nr_of_reties: Number of times to retry the command, defaults to 3
    :type nr_of_reties: int
    :param wait_time: Time to sleep between each retry, defaults to 1
    :type wait_time: float
    :return: The wrapper method.
    :rtype: Any
    """

    def wrapper(
        command: Callable[P, T],
    ) -> Callable[P, T]:
        def command_with_retry(*args: P.args, **kwargs: P.kwargs):
            try:
                return command(*args, **kwargs)
            except Exception as exception:
                logger.exception(exception.args)
                listener = get_listener()
                listener.record(exception.args[0])
                nr_of_retries = 0
                exception_to_raise = None
                while nr_of_retries < nr_of_reties:
                    time.sleep(wait_time)
                    try:
                        logger.warning(f"Retrying {command.__repr__()} for {nr_of_retries}th time")
                        return command(*args, **kwargs)
                    except Exception as exception:
                        nr_of_retries += 1
                        exception_to_raise = exception
                assert exception_to_raise
                raise exception_to_raise

        return command_with_retry

    return wrapper
