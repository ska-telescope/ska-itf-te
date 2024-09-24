"""."""

import logging
from queue import Empty, Queue
from time import time
from typing import Any

from tango import DeviceProxy, EventType

logger = logging.getLogger()


class TMC:
    """Helper class containing TMC specific details such as device names and proxies."""

    def __init__(self):
        """."""
        self.central_node = DeviceProxy("ska_mid/tm_central/central_node")
        self.subarray_node = DeviceProxy("ska_mid/tm_subarray_node/1")
        self.sdp_subarray_leaf_node = DeviceProxy("ska_mid/tm_leaf_node/sdp_subarray01")
        self.csp_master_leaf_node = DeviceProxy("ska_mid/tm_leaf_node/csp_master")
        self.csp_subarray_leaf_node = DeviceProxy("ska_mid/tm_leaf_node/csp_subarray01")

        proxies = [
            self.central_node,
            self.subarray_node,
            self.sdp_subarray_leaf_node,
            self.csp_master_leaf_node,
            self.csp_subarray_leaf_node,
        ]

        self.check_proxies(proxies)

    def get_subarray_node_dp(self, subarray_id) -> DeviceProxy:
        """Get device proxy for a specific subarray node.

        :param subarray_id: _description_
        :type subarray_id: _type_
        :return: _description_
        :rtype: DeviceProxy
        """
        return DeviceProxy(f"ska_mid/tm_subarray_node/{subarray_id}")

    def get_dish_leaf_node_dp(self, dish_id) -> DeviceProxy:
        """Get device proxy for a specific dish leaf node.

        :param dish_id: _description_
        :type dish_id: _type_
        :return: _description_
        :rtype: DeviceProxy
        """
        dish_number = int(dish_id.lower().split("ska", maxsplit=1)[1])
        dp = DeviceProxy(f"ska_mid/tm_leaf_node/d{dish_number:04}")
        assert dp.ping() > 0
        return dp

    def tear_down(self):
        """Tear down the telescope. Bring back to the OFF state."""
        pass

    def check_proxies(self, proxies):
        """Ping device proxies to confirm connectivity.

        :param proxies: _description_
        :type proxies: _type_
        """
        for proxy in proxies:
            assert proxy.ping() > 0


class CBF:
    """Helper class containing CBF specific details such as device names and proxies."""

    def __init__(self):
        """."""
        self.controller = DeviceProxy("mid_csp_cbf/sub_elt/controller")
        self.subarray = DeviceProxy("mid_csp_cbf/sub_elt/subarray_01")
        self.fspcorrsubarray = DeviceProxy("mid_csp_cbf/fspcorrsubarray/01_01")


class CSP:
    """Helper class containing CSP specific details such as device names and proxies."""

    def __init__(self):
        """."""
        self.control = DeviceProxy("mid-csp/control/0")


class Dish:
    """Helper class containing Dish specific details."""

    def __init__(self, sut_namespace: str, dish_id: str):
        """.

        :param sut_namespace: Namespace into which the SUT has been deployed
        :type sut_namespace: str
        :param dish_id: Dish ID with the SKA prefix e.g. SKA001
        :type dish_id: str
        """
        self.sut_namespace = sut_namespace
        self.dish_id = dish_id
        self.dish_tango_host = self.get_dish_tango_host()

    def get_dish_manager_proxy(self) -> DeviceProxy:
        """.

        :return: _description_
        :rtype: DeviceProxy
        """
        dish_number = int(self.dish_id.lower().split("ska", maxsplit=1)[1])
        dp = DeviceProxy(f"{self.dish_tango_host}/mid-dish/dish-manager/ska{dish_number:03}")
        assert dp.ping() > 0
        return dp

    def get_dish_namespace(self) -> str:
        """.

        :return: _description_
        :rtype: str
        """
        if self.sut_namespace in ["staging", "integration"]:
            return f"{self.sut_namespace}-dish-lmc-{str.lower(self.dish_id)}"
        else:
            return f"ci-dish-lmc-{str.lower(self.dish_id)}-{self.sut_namespace[15:]}"

    def get_dish_tango_host(self):
        """.

        :return: _description_
        :rtype: _type_
        """
        dish_namespace = self.get_dish_namespace()
        return f"tango-databaseds.{dish_namespace}.svc.miditf.internal.skao.int:10000"

    def check_proxies(self, proxies):
        """Ping device proxies to confirm connectivity.

        :param proxies: _description_
        :type proxies: _type_
        """
        for proxy in proxies:
            assert proxy.ping() > 0


class EventWaitTimeout(Exception):
    """Exception raised when an event does not occur within a specified timeout."""


def wait_for_event(
    device_proxy: DeviceProxy,
    attr_name: str,
    desired_value: Any,
    event_type: EventType = EventType.CHANGE_EVENT,
    timeout: float = 150.0,
    print_event_details: bool = False,
) -> bool:
    """Wait for a specific type of attribute event to occur.

    Waits and checks changes against desired_value.

    :param device_proxy: Device proxy to be used for event subscription
    :type device_proxy: DeviceProxy
    :param attr_name: Attribute of interest
    :type attr_name: str
    :param desired_value: Expected value for attribute specified with attr_name
    :type desired_value: Any
    :param event_type: Tango event type to wait for, defaults to EventType.CHANGE_EVENT
    :type event_type: EventType
    :param timeout: Maximum period in [s] to wait for desired event, defaults to 150.0
    :type timeout: float
    :param print_event_details: Toggle printing of event data structure, defaults to False
    :type print_event_details: bool
    :raises EventWaitTimeout: _description_
    :return: Success or failure flag indicating whether the attribute changed as desired or not
    :rtype: bool
    """
    # TODO: Report attribute name instead of value where possible

    result = False

    event_queue = Queue()

    event_id = device_proxy.subscribe_event(attr_name, event_type, event_queue.put)

    time_start = time()
    while (time() - time_start) < timeout:
        if not event_queue.empty():
            try:
                event = event_queue.get(timeout=2)
                if print_event_details:
                    logger.debug(f"Received event: {event}")
                assert not event.err, "Event error"

                value = event.attr_value.value
                if value == desired_value:
                    logger.info(
                        f"Device {device_proxy.name()} attribute {attr_name} changed "
                        f"to the following desired value: {desired_value}"
                    )
                    result = True
                    break
            except Empty:
                logger.error("Event queue empty")

    device_proxy.unsubscribe_event(event_id)

    if not result:
        logger.error("Desired event did not occur within the" f"timeout period of {timeout}s")
        raise EventWaitTimeout(
            "Desired event did not occur within the" f"timeout period of {timeout}s"
        )
    return result
