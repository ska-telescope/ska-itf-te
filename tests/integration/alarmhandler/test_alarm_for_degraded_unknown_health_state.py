"""Configure and raise alarm."""

import logging
import os

import httpx
import pytest
from pytest_bdd import given, parsers, scenario, then, when
from ska_control_model import HealthState
from tango import DeviceProxy

from tests.integration.tmc.conftest import wait_for_event

namespace = os.getenv("KUBE_NAMESPACE")

logger = logging.getLogger(__name__)


@pytest.mark.skamid
@scenario(
    "features/configure_healthstate_degraded_unknown.feature",
    "Configure alarm rule for healthState DEGRADED or UNKNOWN",
)
def test_tmc_alarm_for_healthstate_unknown_degraded():
    """Configure and raise alarms.

    This test case is based on real scenario when some devices are not present
    in this case its DishMasters.
    when all are available this scenario might not be the case.
    """


# given
# use @given("a mid telescope") from ..conftest


# given
# use @given("an alarm handler") from ..conftest


@given(
    parsers.parse(
        "an alarm handler is configured to raise an "
        + "alarm when the {device1} {device2} healthState"
    )
)
def configure_alarm_healthstate(response_data, device1, device2):
    """Alarm is configured for DEGRADED or UNKNOWN healthstate.

    :param response_data: fixture for response data
    :param device1: tango device1 for alarm condition
    :param device2: tango device2 for alarm condition
    """
    file_path = os.path.join(
        os.getcwd(),
        "tests/integration/alarmhandler",
        "data/alarm_rules/alarm_rule_healthstate_degraded_unknown.txt",
    )
    with open(file_path, "rb") as file:
        add_api_response = httpx.post(
            f"http://alarm-handler-configurator.{namespace}.svc.miditf.internal.skao.int"
            + ":8004/add-alarms?trl=alarm%2Fhandler%2F01",
            files={"file": ("alarm_rule_healthstate_degraded_unknown.txt", file, "text/plain")},
            data={"trl": "alarm/handler/01"},
        )
        response_data.response = add_api_response.json()
        assert len(response_data.response["alarm_summary"]["tag"]) == 2
        assert f"{device1}" in response_data.response["alarm_summary"]["formula"][0]
        assert f"{device2}" in response_data.response["alarm_summary"]["formula"][0]


# This test case is based on real scenario when some devices are not present
# in this case its Dish Masters.
# when all devices are available this scenario might not be the same.
@when(parsers.parse("{device1} and {device2} remain in healthState DEGRADED or UNKNOWN"))
def check_alarms(device1, device2):
    """Check devices in healthState DEGRADED or UNKNOWN.

    :param device1: tango device1 with healthState DEGRADED or UNKNOWN
    :param device2: tango device2 with healthState DEGRADED or UNKNOWN
    """
    tango_device1 = DeviceProxy(device1)
    tango_device2 = DeviceProxy(device2)
    pytest.device1_result = tango_device1.read_attribute("telescopehealthState").value
    device2_result = tango_device2.read_attribute("healthState").value
    # If the dish is deployed the value will not be DEGRADED
    assert pytest.device1_result in (HealthState.DEGRADED, HealthState.UNKNOWN)
    assert device2_result in (HealthState.DEGRADED, HealthState.UNKNOWN)


@then("alarm for healthState DEGRADED or UNKNOWN must be raised with UNACKNOWLEDGE state")
def check_alarm_state(response_data):
    """Check alarm state.

    :param response_data: fixture for response data
    """
    alarm_handler = DeviceProxy("alarm/handler/01")
    alarm_tag = response_data.response["alarm_summary"]["tag"]
    if pytest.device1_result == HealthState.DEGRADED:
        alarm_tag = tuple([alarm_tag[0]])
    elif pytest.device1_result == HealthState.UNKNOWN:
        alarm_tag = tuple([alarm_tag[1]])
    assert wait_for_event(
        alarm_handler, "alarmUnacknowledged", alarm_tag, print_event_details=True, timeout=250.0
    )
    # acknowledge the alarm
    alarm_handler.Ack(alarm_tag)
