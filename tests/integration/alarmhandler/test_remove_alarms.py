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
def check_configured_tag(tag_name):
    """Check configured alarm with given tag.

    :param tag_name: alarm tag
    """
    file_path = os.path.join(
        os.getcwd(), "tests/integration/alarmhandler/data/alarm_rules/alarm_file1.txt"
    )
    with open(file_path, "rb") as file:
        response = httpx.post(
            f"http://alarm-handler-configurator.{namespace}.svc.miditf.internal.skao.int"
            + ":8004/add-alarms?fqdn=alarm%2Fhandler%2F01",
            files={"file": ("alarm_file1.txt", file, "text/plain")},
            data={"fqdn": "alarm/handler/01"},
        )
        logging.info(response)
        response_data = response.json()
        assert len(response_data["alarm_summary"]["tag"]) == 1
        assert response_data["alarm_summary"]["tag"] == [tag_name]


@when(parsers.parse("I remove configured TMC alarm tag {tag_name} using alarm configurator tool"))
def remove_alarms_api(tag_name):
    """Call remove-alarms API.

    :param tag_name: alarm tag name to remove
    """
    response = httpx.post(
        f"http://alarm-handler-configurator.{namespace}.svc.miditf.internal.skao.int."
        + f"local:8004/remove-alarm?tag={tag_name}&"
        + "alarmhandlerfqdn=alarm%2Fhandler%2F01",
        data={
            "tag": tag_name,
            "alarmhandlerfqdn": "alarm/handler/01",
        },
    )
    response_data = response.json()
    logging.info(response_data)


@then(parsers.parse("TMC alarm tag {tag_name}is removed successfully"))
def check_alarms(response_data, tag_name):
    """Check add-alarms API response.

    :param response_data: json received from remove-alarm API
    :param tag_name: alarm tag to remove
    """
    assert response_data["alarm_summary"] is not tag_name
