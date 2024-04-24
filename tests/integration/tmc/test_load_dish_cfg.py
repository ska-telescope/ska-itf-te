"""TMC LoadDishCfg tests."""

import json
import time
from typing import Iterator

import pytest
from pytest_bdd import given, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.base import AbstractDeviceProxy
from ska_ser_skallop.mvp_control.describing import mvp_names as names


@pytest.fixture(name="online_csp_controller")
def fxt_online_csp_controller() -> Iterator[AbstractDeviceProxy]:
    """
    Switch the CSP Controller to ONLINE state, yield it and put it back into DISABLE afterwards.

    :yield: CSP Controller DeviceProxy
    :rtype: Generator[AbstractDeviceProxy]
    """
    tel = names.TEL()
    csp = con_config.get_device_proxy(tel.csp.controller)
    csp.adminMode = 0
    wait_for_state(csp, "OFF")
    yield csp
    csp.adminMode = 1
    wait_for_state(csp, "DISABLE")


@pytest.fixture(name="tmc_central_node")
def fxt_tmc_central_node() -> Iterator[AbstractDeviceProxy]:
    """
    Yield the TMC central node DeviceProxy.

    :yield: TMC central node DeviceProxy
    :rtype: Generator[AbstractDeviceProxy]
    """
    tel = names.TEL()
    tmc = con_config.get_device_proxy(tel.tm.central_node)
    yield tmc


@pytest.fixture(name="cbf_initsysparam")
def fxt_cbf_initsysparam() -> Iterator[str]:
    """
    Yield the CBF InitSysPrams as a JSON string.

    :yield: The CBF InitSysPrams in JSON.
    :rtype: Generator[str]
    """
    params = {
        "interface": "https://schema.skao.int/ska-mid-cbf-initsysparam/1.0",
        "tm_data_sources": [
            "car://gitlab.com/ska-telescope/ska-telmodel-data?ska-sdp-tmlite-repository-1.0.0#tmdata"  # noqa: E501
        ],
        "tm_data_filepath": "instrument/ska1_mid_psi/ska-mid-cbf-system-parameters.json",
    }
    yield json.dumps(params)


@pytest.fixture(name="expected_dish_vcc_validation_status")
def fxt_expected_dish_vcc_validation_status() -> Iterator[str]:
    """
    Yield the expected dish VCC validation status.

    :yield: The expected dish VCC validation status.
    :rtype: Iterator[str]
    """
    expected = {
        "dish": "ALL DISH OK",
        "ska_mid/tm_leaf_node/csp_master": "TMC and CSP Master Dish Vcc Version is Same",
    }
    yield json.dumps(expected)


@pytest.mark.xfail(reason="See SKB-338")
@pytest.mark.order(1)
@pytest.mark.tmc
@pytest.mark.skamid
@pytest.mark.load_dish_cfg
@scenario("features/tmc_load_dish_cfg.feature", "Load dish cfg from the TMC")
def test_load_dish_cfg_from_tmc():
    """
    Load dish cfg from the TMC.

    This test is specified to run first because the bug is only encountered on a fresh deployment.
    """


@given("a TMC central node in adminMode OFFLINE and ON state")
def a_tmc_central_node_in_adminmode_offline_and_on_state(tmc_central_node: AbstractDeviceProxy):
    """
    Assert that the TMC central node is in adminMode OFFLINE and ON state.

    :param tmc_central_node: The TMC central node DeviceProxy
    :type tmc_central_node: AbstractDeviceProxy
    """
    assert str(tmc_central_node.State()) == "ON"
    assert str(tmc_central_node.adminMode) == "adminMode.OFFLINE"


@given("a CSP LMC in ONLINE adminMode and OFF state")
def a_csp_lmc_in_online_adminmode_and_off_state(online_csp_controller: AbstractDeviceProxy):
    """
    Put the CSP LMC in adminMode ONLINE and assert that it reaches state OFF.

    :param online_csp_controller: the CSP LMC controller DeviceProxy
    :type online_csp_controller: AbstractDeviceProxy
    """
    assert str(online_csp_controller.State()) == "OFF"
    assert str(online_csp_controller.adminMode) == "adminMode.ONLINE"


@when("I command it to LoadDishCfg")
def i_command_it_to_loaddishcfg(tmc_central_node: AbstractDeviceProxy, cbf_initsysparam: str):
    """
    Run the LoadDishCfg command.

    :param tmc_central_node: The TMC central node DeviceProxy
    :type tmc_central_node: AbstractDeviceProxy
    :param cbf_initsysparam: the CBF MCS initsysparams
    :type cbf_initsysparam: str
    """
    tmc_central_node.LoadDishCfg(cbf_initsysparam)


@then("the DishVccValidationStatus attribute command must be in the OK state")
def the_dishvccvalidationstatus_attribute_command_must_be_in_the_ok_state(
    tmc_central_node: AbstractDeviceProxy, expected_dish_vcc_validation_status: str
):
    """
    Verify that the DishVccValidationStatus reaches the expected state.

    :param tmc_central_node: The TMC Central Node DeviceProxy.
    :type tmc_central_node: AbstractDeviceProxy
    :param expected_dish_vcc_validation_status: The expected dish vcc validation status.
    :type expected_dish_vcc_validation_status: str
    """
    assert tmc_central_node.DishVccValidationStatus == expected_dish_vcc_validation_status


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
