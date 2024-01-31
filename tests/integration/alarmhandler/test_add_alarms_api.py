"""This module is used for testing Alarm-Handler configurator add-alarms API."""
import logging
import os

import httpx
import pytest
from pytest_bdd import parsers, scenario, then, when

namespace = os.getenv("KUBE_NAMESPACE")

logger = logging.getLogger(__name__)


@pytest.mark.skamid
@scenario("features/add_alarms.feature", "Configure TMC alarms")
def test_tmc_mid_configure_alarms():
    """Configure tmc mid alarms."""


# given
# use @given("a TMC") from ..conftest


# given
# use @given("an alarm handler") from ..conftest


@when(
    parsers.parse(
        "I configure alarms with {alarm_rule_file} for TMC using alarm configurator tool"
    )
)
def add_alarms_api(alarm_rule_file):
    """Call add-alarms API.

    :param alarm_rule_file: alarm rules file as input for add-alarms API
    """
    with open(f"../alarmhandler/data/alarm_rules/{alarm_rule_file}", "rb") as file:
        response = httpx.post(
            f"http://alarm-handler-configurator.{namespace}.svc.miditf.internal.skao.int."
            + "local:8004/add-alarms?fqdn=alarm%2Fhandler%2F01",
            files={"file": (alarm_rule_file, file, "text/plain")},
            data={"fqdn": "alarm/handler/01"},
        )
        logging.info(response)
        response_data = response.json()
        logging.info(response_data)


@then("TMC alarms are configured successfully")
def check_alarms(response_data):
    """Check add-alarms API response.

    :param response_data: json received from add-alarms API
    """
    assert len(response_data["alarm_summary"]["tag"]) == 1
    assert response_data["alarm_summary"]["tag"] == [
        "subarraynode_obsstate_fault",
    ]


# TODO: add tear down
