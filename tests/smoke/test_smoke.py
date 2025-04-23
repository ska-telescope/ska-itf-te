"""."""

import logging

from tango import DeviceProxy

logger = logging.getLogger()


def test_devices_reachable():
    """Tests connectivity to tango devices.

    This is a simple smoke test to check if the required devices are reachable.
    It creates device proxies to various tango devices and checks if they are reachable.
    """
    device = DeviceProxy(
        "tango-databaseds.ska-mid-central-controller.svc.mid.internal.skao.int"
        ":10000/mid-tmc/central-node/0"
    )

    assert device.ping(), "Device is not reachable"
    logger.info("Devices reachable")
