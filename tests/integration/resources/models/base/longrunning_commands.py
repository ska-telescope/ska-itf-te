"""."""

from ska_ser_skallop.event_handling.handlers import WaitForLRCComplete
from ska_ser_skallop.utils.singleton import Memo


class WithCommandID:
    """."""

    def __init__(self) -> None:
        """_summary_."""
        self._long_running_command_subscriber = None

    @property
    def long_running_command_subscriber(self) -> WaitForLRCComplete | None:
        """_summary_.

        :return: _description_
        :rtype: WaitForLRCComplete | None
        """
        return Memo().get("long_running_command_subscriber")

    @long_running_command_subscriber.setter
    def long_running_command_subscriber(self, subscriber: WaitForLRCComplete):
        """_summary_.

        :param subscriber: _description_
        :type subscriber: WaitForLRCComplete
        """
        Memo(long_running_command_subscriber=subscriber)
