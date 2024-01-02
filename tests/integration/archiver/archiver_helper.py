"""Archiver helper functionality."""
from time import sleep
from typing import Any, Union

from tango import AttributeProxy, ConnectionFailed, DeviceProxy


class ArchiverHelper:
    """ArchiverHelper."""

    def __init__(self, conf_manager, eventsubscriber):
        """
        Initialise the ArchiverHelper.

        :param conf_manager: The configuration manager.
        :param eventsubscriber: The event subscriber.
        """
        self.conf_manager = conf_manager
        self.eventsubscriber = eventsubscriber
        self.conf_manager_proxy = get_proxy(self.conf_manager)
        self.evt_subscriber_proxy = get_proxy(self.eventsubscriber)

    def attribute_add(self, fqdn, strategy, polling_period, value):
        """
        Add the specified attribute to the archive configuration.

        :param fqdn: Fully qualified domain name of the attribute to be added.
        :type fqdn: str
        :param polling_period: Polling period in milliseconds.
        :type polling_period: int
        :param strategy: strategy for archiving.
        :type strategy: str
        :param value: value for  strategy specified.
        :type value: Union[ int , bool]
        :return: True or False
        """
        if not self.is_already_archived(fqdn):
            AttributeProxy(fqdn).read()
            self.conf_manager_proxy.write_attribute("SetAttributeName", fqdn)
            self.conf_manager_proxy.write_attribute("SetArchiver", self.eventsubscriber)
            self.conf_manager_proxy.write_attribute("SetStrategy", "ALWAYS")
            self.conf_manager_proxy.write_attribute(strategy, value)
            if polling_period:
                self.conf_manager_proxy.write_attribute("SetPollingPeriod", int(polling_period))
            self.conf_manager_proxy.AttributeAdd()
            return True
        return False

    def attribute_list(self):
        """
        Retrieve the attribute list.

        :return: Attribute list
        """
        return self.evt_subscriber_proxy.AttributeList

    def is_already_archived(self, fqdn):
        """
        Check if the attribute is already archived.

        :param fqdn: Fully qualified domain name of the attribute to be added.
        :type fqdn: str
        :return: True if attribute is already archived
        """
        attr_list = self.attribute_list()
        if attr_list is not None:
            for already_archived in attr_list:
                if fqdn in str(already_archived).lower():
                    return True
        return False

    def start_archiving(
        self,
        fqdn: str = None,
        strategy: str = None,
        polling_period: int = 1000,
        value: Union[int, bool] = None,
    ) -> Any:
        """
        Initialize the archiving process.

        :param fqdn: Fully qualified domain name of the attribute to be added, defaults to None
        :type fqdn: str
        :param strategy: Strategy for archiving, defaults to None
        :type strategy: str
        :param polling_period: Polling period in milliseconds, defaults to 1000
        :type polling_period: int
        :param value: value for given strategy, defaults to None
        :type value: Union[ int, bool]
        :return: Start on archiver.
        :rtype: Any
        """
        if fqdn is not None:
            self.attribute_add(fqdn, strategy, polling_period, value)
        return self.evt_subscriber_proxy.Start()

    def stop_archiving(self, fqdn):
        """
        Stop the archiving process.

        :param fqdn: Fully qualified domain name of the attribute to be added.
        :type fqdn: str
        :return: removed attribute
        """
        self.evt_subscriber_proxy.AttributeStop(fqdn)
        return self.conf_manager_proxy.AttributeRemove(fqdn)

    def evt_subscriber_attribute_status(self, fqdn):
        """
        Retrieve event subscriber attribute status.

        :param fqdn: Fully qualified domain name of the attribute to be added.
        :type fqdn: str
        :return: event subscriber attribute status
        """
        return self.evt_subscriber_proxy.AttributeStatus(fqdn)

    def conf_manager_attribute_status(self, fqdn):
        """
        Retrieve configuration manager attribute status.

        :param fqdn: Fully qualified domain name of the attribute to be added.
        :type fqdn: str
        :return: configuration manager attribute status
        """
        return self.conf_manager_proxy.AttributeStatus(fqdn)

    def is_started(self, fqdn):
        """
        Determine whether archiving has started.

        :param fqdn: Fully qualified domain name of the attribute to be added.
        :type fqdn: str
        :return: status
        """
        return "Archiving          : Started" in self.evt_subscriber_attribute_status(fqdn)

    def wait_for_start(self, fqdn, sleep_time=0.1, max_retries=30):
        """
        Wait for archiver to start.

        :param fqdn: Fully qualified domain name of the attribute to be added.
        :type fqdn: str
        :param sleep_time: Default is 0.1
        :param max_retries: Default is 30
        :return: total sleep time
        """
        total_sleep_time = 0
        for _ in range(0, max_retries):
            try:
                if "Archiving          : Started" in self.conf_manager_attribute_status(fqdn):
                    break
            except Exception:
                pass
            sleep(sleep_time)
            total_sleep_time += 1
        return total_sleep_time * sleep_time


def get_proxy(device_name: str, retries: int = 3):
    """
    Retrieve the proxy.

    Retry if connection fails during proxy creation

    :param device_name: device name
    :type device_name: str
    :param retries: no of retries to create proxy
    :type retries: int
    :return: device proxy
    :raises ConnectionFailed: raises connection failed exception.
    """
    retry = 0
    no_of_retries = retries
    while retry <= no_of_retries:
        try:
            return DeviceProxy(device_name)
        except ConnectionFailed as connection_failed:
            retry += 1
            if retry == 4:
                raise connection_failed
            sleep(10)
