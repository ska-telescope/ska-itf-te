"""load and acknowledge the configured alarms."""
import logging
import os

import httpx
import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.event_handling.builders import get_message_board_builder
from tango import DeviceProxy

namespace = os.getenv("KUBE_NAMESPACE")

logger = logging.getLogger(__name__)


@pytest.mark.skamid
@scenario("features/configure_unknown_state_alarm.feature", "Configure Alarm for UNKNOWN State")
def test_tmc_alarm_for_state_unknown():
    """Configure and raise alarms."""


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
            + ":8004/add-alarms?fqdn=alarm%2Fhandler%2F01",
            files={"file": ("alarm_rule_healthstate_unknown.txt", file, "text/plain")},
            data={"fqdn": "alarm/handler/01"},
        )
        response_data.response = add_api_response.json()
        assert len(response_data.response["alarm_summary"]["tag"]) == 1
        assert f"{device1}" in response_data.response["alarm_summary"]["formula"]
        assert f"{device2}" in response_data.response["alarm_summary"]["formula"]


@when(parsers.parse("{device1} and {device2} remain in healthState UNKNOWN for long"))
def check_alarms(device1, device2):
    """Check devices in healthState UNKNOWN.

    :param device1: tango device1 with healthState UNKNOWN
    :param device2: tango device2 with healthState UNKNOWN
    """
    tango_device1 = con_config.get_device_proxy(device1)
    tango_device2 = con_config.get_device_proxy(device2)
    result = tango_device1.read_attribute("telescopehealthState").value
    result = tango_device2.read_attribute("healthState").value
    assert_that(str(result)).is_equal_to("UNKNOWN")


@then("alarm for healthState UNKNOWN must be raised with UNACKNOWLEDGE state")
def check_alarm_state(response_data, state_value):
    """Check alarm state.

    :param response_data: fixture for response data
    :param state_value: tango device attribute value alarm condition
    """
    alarm_handler = DeviceProxy("alarm/handler/01")
    alarm_tag = response_data.response["alarm_summary"]["tag"]
    brd = get_message_board_builder()
    brd.set_waiting_on("alarm/handler/01").for_attribute("alarmUnacknowledged").to_become_equal_to(
        alarm_tag.lower(),
    )
    # acknowledge the alarm
    alarm_handler.Ack(alarm_tag.lower())
