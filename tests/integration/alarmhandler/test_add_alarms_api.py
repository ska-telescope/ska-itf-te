"""This module is used for testing Alarm-Handler configurator API."""
import logging
import os

import httpx
import pytest
from pytest_bdd import given, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names

namespace = os.getenv("KUBE_NAMESPACE")

logger = logging.getLogger(__name__)


@pytest.mark.skamid
@scenario("features/add_alarms.feature", "Configure TMC alarms")
def test_tmc_mid_configure_alarms():
    """Configure tmc mid alarms."""


@given("a TMC")
def a_tmc():
    """Given a TMC."""
    tel = names.TEL()
    nr_of_subarrays = 1

    central_node_name = tel.tm.central_node
    central_node = con_config.get_device_proxy(central_node_name)
    result = central_node.ping()
    assert result > 0

    subarray_node = con_config.get_device_proxy(tel.tm.subarray(1))
    result = subarray_node.ping()
    assert result > 0

    csp_master_leaf_node = con_config.get_device_proxy(tel.tm.csp_leaf_node)
    result = csp_master_leaf_node.ping()
    assert result > 0

    sdp_master_leaf_node = con_config.get_device_proxy(tel.tm.sdp_leaf_node)
    result = sdp_master_leaf_node.ping()
    assert result > 0

    csp_subarray_leaf_node = con_config.get_device_proxy(tel.tm.subarray(1).csp_leaf_node)
    result = csp_subarray_leaf_node.ping()
    assert result > 0

    sdp_subarray_leaf_node = con_config.get_device_proxy(tel.tm.subarray(1).sdp_leaf_node)
    result = sdp_subarray_leaf_node.ping()
    assert result > 0

    if tel.skamid:
        for index in range(1, nr_of_subarrays + 1):
            dish_leaf_nodes = con_config.get_device_proxy(tel.tm.dish_leafnode(index))
            result = dish_leaf_nodes.ping()
            assert result > 0


@given("an alarm handler")
def a_alarm_handler():
    """Given an alarm handler."""
    alarm_handler = con_config.get_device_proxy("alarm/handler/01")
    result = alarm_handler.ping()
    result > 0


@when("I configure alarms for TMC using alarm configurator tool")
def add_alarms_api():
    """Call add alarms API."""
    with open(f"/app/tests/alarmhandler/data/alarm_rules/alarm_file1.txt", "rb") as file:
        response = httpx.post(
            f"http://alarm-handler-configurator.{namespace}.svc.miditf.internal.skao.int."
            + "local:8004/add-alarms?fqdn=alarm%2Fhandler%2F01",
            files={"file": ("alarm_file1.txt", file, "text/plain")},
            data={"fqdn": "alarm/handler/01"},
        )
        logging.info(response)
        response_data = response.json()
        logging.info(response_data)


@then("TMC alarms are successfully configured")
def check_alarms(response_data):
    """Check add alarms API response.

    :param response_data: json received from add-alarms API
    """
    assert len(response_data["alarm_summary"]["tag"]) == 1
    assert response_data["alarm_summary"]["tag"] == [
        "subarraynode_obsstate_fault",
    ]
