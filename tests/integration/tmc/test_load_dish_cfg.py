"""Configure scan on subarray feature tests."""

import json
import time

import pytest
from pytest_bdd import given, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.base import AbstractDeviceProxy
from ska_ser_skallop.mvp_control.describing import mvp_names as names


@pytest.mark.order(1)
@pytest.mark.tmc
@pytest.mark.skamid
@pytest.mark.load_dish_cfg
@scenario("features/tmc_load_dish_cfg.feature", "Load dish cfg from the TMC")
def test_load_dish_cfg_from_tmc():
    """Load dish cfg from the TMC."""


@given("a TMC central node in adminMode OFFLINE and ON state")
def a_tmc_central_node_in_adminmode_offline_and_on_state():
    """Assert that the TMC central node is in adminMode OFFLINE and ON state."""
    tel = names.TEL()
    tmc = con_config.get_device_proxy(tel.tm.central_node)
    assert str(tmc.State()) == "ON"
    assert str(tmc.adminMode) == "adminMode.OFFLINE"


@given("a CSP LMC in ONLINE adminMode and OFF state")
def a_csp_lmc_in_online_adminmode_and_off_state():
    """Put the CSP LMC in adminMode ONLINE and assert that it reaches state OFF."""
    tel = names.TEL()
    csp = con_config.get_device_proxy(tel.csp.controller)
    csp.adminMode = 0
    wait_for_state(csp, "OFF")
    assert str(csp.State()) == "OFF"
    assert str(csp.adminMode) == "adminMode.ONLINE"


@when("I command it to LoadDishCfg")
def i_command_it_to_loaddishcfg():
    """Run the LoadDishCfg command."""
    tel = names.TEL()
    central_node = con_config.get_device_proxy(tel.tm.central_node)
    dish_cfg = {
        "interface": "https://schema.skao.int/ska-mid-cbf-initsysparam/1.0",
        "tm_data_sources": [
            "car://gitlab.com/ska-telescope/ska-telmodel-data?ska-sdp-tmlite-repository-1.0.0#tmdata"  # noqa: E501
        ],
        "tm_data_filepath": "instrument/ska1_mid_psi/ska-mid-cbf-system-parameters.json",
    }
    central_node.LoadDishCfg(json.dumps(dish_cfg))


@then("the DishVccValidationStatus attribute command must be in the OK state")
def the_dishvccvalidationstatus_attribute_command_must_be_in_the_ok_state():
    """Verify that the DishVccValidationStatus reaches the expected state."""
    tel = names.TEL()
    central_node = con_config.get_device_proxy(tel.tm.central_node)
    expected = json.dumps(
        {
            "dish": "ALL DISH OK",
            "ska_mid/tm_leaf_node/csp_master": "TMC and CSP Master Dish Vcc Version is Same",
        }
    )
    assert central_node.DishVccValidationStatus == expected


def wait_for_state(device_proxy: AbstractDeviceProxy, state: str, max_sleep=60):
    """
    Wait for the DeviceProxy to reach the expected state.

    :param device_proxy: the DeviceProxy
    :type device_proxy: AbstractDeviceProxy
    :param state: the DevState to reach
    :type state: str
    :param max_sleep: the maximum time to sleep in seconds.
    :type max_sleep: int
    :raises TimeoutError: if the DeviceProxy does not reach the expected state
    """
    sleep_interval = 1
    total_sleep = 0
    while str(device_proxy.State()) != state:
        time.sleep(sleep_interval)
        total_sleep += sleep_interval
        if total_sleep >= max_sleep:
            raise TimeoutError(
                f"{device_proxy.dev_name()} failed to reach state '{state}' "
                f"after {total_sleep} seconds; current state={device_proxy.State()}"
            )
        sleep_interval = min(2 * sleep_interval, max_sleep - total_sleep)
