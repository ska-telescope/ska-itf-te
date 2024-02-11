"""This module is used for testing Alarm-Handler configurator remove-alarms API."""
import logging
import os

import httpx
import pytest
from pytest_bdd import given, parsers, scenario, then, when

namespace = os.getenv("KUBE_NAMESPACE")

logger = logging.getLogger(__name__)


@pytest.mark.skamid
@scenario("features/remove_alarms.feature", "Remove TMC Alarms")
def test_tmc_mid_remove_alarms():
    """Remove tmc mid alarms."""


# given
# use @given("a TMC") from ..conftest


# given
# use @given("an alarm handler") from ..conftest


@given(parsers.parse("TMC alarm is configured with tag {tag_name}"))
def check_configured_tag(response_data, tag_name):
    """Check configured alarm with given tag.

    :param response_data: fixture for responce data
    :param tag_name: alarm tag
    """
    file_path = os.path.join(
        os.getcwd(), "tests/integration/alarmhandler/data/alarm_rules/alarm_rule1.txt"
    )
    with open(file_path, "rb") as file:
        add_api_response = httpx.post(
            f"http://alarm-handler-configurator.{namespace}.svc.miditf.internal.skao.int"
            + ":8004/add-alarms?fqdn=alarm%2Fhandler%2F01",
            files={"file": ("alarm_rule1.txt", file, "text/plain")},
            data={"fqdn": "alarm/handler/01"},
        )
        response_data.response = add_api_response.json()
        assert len(response_data.response["alarm_summary"]["tag"]) == 1
        assert response_data.response["alarm_summary"]["tag"] == [tag_name]


@when(parsers.parse("I remove configured TMC alarm tag {tag_name} using alarm configurator tool"))
def remove_alarms_api(response_data, tag_name):
    """Call remove-alarms API.

    :param response_data: fixture for response data
    :param tag_name: alarm tag name to remove
    """
    remove_api_response = httpx.post(
        f"http://alarm-handler-configurator.{namespace}.svc.miditf.internal.skao.int"
        + f":8004/remove-alarm?tag={tag_name}&"
        + "alarmhandlerfqdn=alarm%2Fhandler%2F01",
        data={
            "tag": tag_name,
            "alarmhandlerfqdn": "alarm/handler/01",
        },
    )
    response_data.response = remove_api_response.json()


@then(parsers.parse("TMC alarm tag {tag_name}is removed successfully"))
def check_alarms(response_data, tag_name):
    """Check add-alarms API response.

    :param response_data: fixture for response data
    :param tag_name: alarm tag to remove
    """
    assert (
        f"Alarm with tags {tag_name}is removed successfully" in response_data.response["message"]
    )
