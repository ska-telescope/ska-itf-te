"""Validation utility."""
from ska_control_model import ResultCode


class CommandException(Exception):
    """Fail with an exception.

    :param: Exception: _description_
    """

    def __init__(self, result: tuple[ResultCode, str]) -> None:
        """Init Object.

        :param result: ResultCode as input
        """
        arg = f"Command failed (code {result[0]} with message {result[1]})"
        super().__init__(arg)


def command_success(result: tuple[list[ResultCode], list[str]]):
    """Return successfully if command result code is in the list of expected results.

    :param result: Tuple of ResultCode values.

    :return: command_status: Whether or not the command succeeded
    """
    command_status = result[0][0]
    return command_status in [
        ResultCode.ABORTED,
        ResultCode.OK,
        ResultCode.QUEUED,
        ResultCode.STARTED,
    ]
