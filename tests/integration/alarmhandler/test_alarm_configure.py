"""load and acknowledge the configured alarms."""
import logging
import os

import httpx
import pytest

from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names

# from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from tango import DeviceProxy

namespace = os.getenv("KUBE_NAMESPACE")

logger = logging.getLogger(__name__)


@pytest.mark.skamid
@scenario("features/configure_alarms.feature", "Configure Alarm for UNKNOWN State")
def test_tmc_alarm_for_state_unknown():
    """Configure and raise alarms."""


# given
# use @given("a mid telescope") from ..conftest


# given
# use @given("an alarm handler") from ..conftest


@given(
    parsers.parse(
        "an alarm handler is configured to raise an alarm when the "
        + "{device_name} State {state_value}"
    )
)
def configure_alarm_state(response_data, device_name, state_value):
    """Alarm is configured for UNKNOWN state.

    :param response_data: fixture for response data
    :param device_name: tango device for alarm condition
    :param state_value: tango device attribute value for alarm condition
    """
    file_path = os.path.join(
        os.getcwd(), "tests/integration/alarmhandler/data/alarm_rules/alarm_rule_state_unknown.txt"
    )
    logging.info(file_path)
    with open(file_path, "rb") as file:
        add_api_response = httpx.post(
            f"http://alarm-handler-configurator.{namespace}.svc.miditf.internal.skao.int"
            + ":8004/add-alarms?fqdn=alarm%2Fhandler%2F01",
            files={"file": ("alarm_rule_state_unknown.txt", file, "text/plain")},
            data={"fqdn": "alarm/handler/01"},
        )
        logging.info(add_api_response)
        response_data.response = add_api_response.json()
        logging.info(response_data.response)
        assert len(response_data.response["alarm_summary"]["tag"]) == 1
        assert response_data.response["alarm_summary"]["tag"] == [
            f"{device_name.lower()}_telescopestate_{state_value.lower()}",
        ]


@when("telescope remains in UNKNOWN state for long")
def check_alarms():
    """Check telescope in UNKNOWN."""
    tel = names.TEL()
    central_node = con_config.get_device_proxy(tel.tm.central_node)
    result = central_node.read_attribute("telescopeState").value
    assert_that(str(result)).is_equal_to("UNKNOWN")


@then("alarm must be raised with UNACKNOWLEDGE state")
def check_alarm_state(response_data):
    """Check alarm state.

    :param response_data: fixture for response data
    """
    logging.info(response_data.response)
    alarm_handler = DeviceProxy("alarm/handler/01")
    ah_result = alarm_handler.read_attribute("alarmUnacknowledged")
    logging.info(ah_result)
    assert response_data.response["alarm_summary"]["state"] == [
        "UNACK",
    ]
    alarm_handler.Ack(response_data.response["alarm_summary"]["tag"])