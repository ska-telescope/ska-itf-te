"""Configure and raise alarm."""

import logging
import os

import httpx
import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_control_model import HealthState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.event_handling.builders import get_message_board_builder
from tango import DeviceProxy

namespace = os.getenv("KUBE_NAMESPACE")

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="intermittently failing test")  # TEMPORARY COMMIT
@pytest.mark.skamid
@scenario(
    "features/configure_healthstate_unknown.feature",
    "Configure alarm rule for healthState UNKNOWN",
)
def test_tmc_alarm_for_healthstate_unknown():
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
    """Alarm is configured for UNKNOWN healthstate.

    :param response_data: fixture for response data
    :param device1: tango device1 for alarm condition
    :param device2: tango device2 for alarm condition
    """
    file_path = os.path.join(
        os.getcwd(),
        "tests/integration/alarmhandler/data/alarm_rules/alarm_rule_healthstate_unknown.txt",
    )
    with open(file_path, "rb") as file:
        add_api_response = httpx.post(
            f"http://alarm-handler-configurator.{namespace}.svc.miditf.internal.skao.int"
            + ":8004/add-alarms?trl=alarm%2Fhandler%2F01",
            files={"file": ("alarm_rule_healthstate_unknown.txt", file, "text/plain")},
            data={"trl": "alarm/handler/01"},
        )
        response_data.response = add_api_response.json()
        assert len(response_data.response["alarm_summary"]["tag"]) == 1
        assert f"{device1}" in response_data.response["alarm_summary"]["formula"][0]
        assert f"{device2}" in response_data.response["alarm_summary"]["formula"][0]


# This test case is based on real scenario when some devices are not present
# in this case its Dish Masters.
# when all devices are available this scenario might not be the same.
@when(parsers.parse("{device1} and {device2} remain in healthState UNKNOWN for long"))
def check_alarms(device1, device2):
    """Check devices in healthState UNKNOWN.

    :param device1: tango device1 with healthState UNKNOWN
    :param device2: tango device2 with healthState UNKNOWN
    """
    tango_device1 = con_config.get_device_proxy(device1)
    tango_device2 = con_config.get_device_proxy(device2)
    device1_result = tango_device1.read_attribute("telescopehealthState").value
    device2_result = tango_device2.read_attribute("healthState").value
    # If the dish is deployed the value will not be UNKNOWN
    assert_that(device1_result).is_equal_to(HealthState.UNKNOWN)
    assert_that(device2_result).is_equal_to(HealthState.UNKNOWN)


@then("alarm for healthState UNKNOWN must be raised with UNACKNOWLEDGE state")
def check_alarm_state(response_data):
    """Check alarm state.

    :param response_data: fixture for response data
    """
    alarm_handler = DeviceProxy("alarm/handler/01")
    alarm_tag = response_data.response["alarm_summary"]["tag"]
    brd = get_message_board_builder()
    # If the dish is deployed the alarm will not be raised
    brd.set_waiting_on("alarm/handler/01").for_attribute("alarmUnacknowledged").to_become_equal_to(
        alarm_tag,
    )
    # acknowledge the alarm
    alarm_handler.Ack(alarm_tag)
