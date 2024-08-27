"""Configure scan via TMC feature tests."""

from pytest_bdd import given, scenario, then, when
import os
from tango import DeviceProxy, EventType
import json
import pytest
from queue import Queue, Empty


def wait_until(device_proxy, attr_name, desired_value, event_type, n_events):
    event_queue = Queue()

    device_proxy.subscribe_event(attr_name, event_type, lambda event: event_queue.put(event))

    try:
        for _ in range(n_events):
            event = event_queue.get(timeout=10)
            print(f"Received event: {event}")
            assert event.err == False, "Event error"

            value = event.attr_value.value
            if value == desired_value:
                print("Attribute changed to the desired value.")
                break
    except Empty:
        pytest.fail("isDishVccConfigSet change event did not occur within timeout period")


@scenario("features/tmc_configure_scan.feature", "Configure scan via TMC on 1 subarray in mid")
def test_configure_scan_via_tmc_on_1_subarray_in_mid():
    """Configure scan via TMC on 1 subarray in mid."""


@pytest.fixture(autouse=True, scope="session")
def tango_host():
    CURRENT_TANGO_HOST = os.environ.get("TANGO_HOST")
    CLUSTER_DOMAIN = "miditf.internal.skao.int"
    SUT_NAMESPACE = "integration"
    RECEPTORS = ["SKA001", "SKA036"]

    if SUT_NAMESPACE in ["staging", "integration"]:
        SKA001_NAMESPACE = (
            f"{SUT_NAMESPACE}-dish-lmc-ska001"  # ci-dish-lmc-ska001-at-2139-tmc-0-20-1-integration
        )
        SKA036_NAMESPACE = (
            f"{SUT_NAMESPACE}-dish-lmc-ska036"  # ci-dish-lmc-ska036-at-2139-tmc-0-20-1-integration
        )
    else:
        SKA001_NAMESPACE = f"ci-dish-lmc-ska001-{SUT_NAMESPACE[15:]}"  # ci-dish-lmc-ska001-at-2139-tmc-0-20-1-integration
        SKA036_NAMESPACE = f"ci-dish-lmc-ska036-{SUT_NAMESPACE[15:]}"  # ci-dish-lmc-ska036-at-2139-tmc-0-20-1-integration

    TANGO_HOST = f"tango-databaseds.{SUT_NAMESPACE}.svc.{CLUSTER_DOMAIN}:10000"
    os.environ["TANGO_HOST"] = TANGO_HOST
    yield
    if CURRENT_TANGO_HOST:
        os.environ["TANGO_HOST"] = CURRENT_TANGO_HOST


@given("a TMC configured with 1 subarray", target_fixture="tmc")
def _():
    """a TMC configured with 1 subarray."""
    print("Getting TMC DeviceProxies")

    tmc_central_node = DeviceProxy("ska_mid/tm_central/central_node")
    tmc_subarray = DeviceProxy("ska_mid/tm_subarray_node/1")

    assert tmc_central_node.ping() > 0
    assert tmc_subarray.ping() > 0

    return tmc_central_node, tmc_subarray


@given("a CSP in adminMode online", target_fixture="csp")
def _():
    """a CSP in adminMode online"""
    print("Getting CSP DeviceProxy and setting online")
    csp_control = DeviceProxy("mid-csp/control/0")

    csp_control.adminMode = 0


@when("I turn the telescope ON")
def _(tmc, csp):
    """I turn the telescope ON."""
    print("Turning telescope ON")

    DATA_DIR = "../resources/data"
    CBF_CONFIGS = f"{DATA_DIR}/cbf"
    DISH_CONFIG_FILE = f"{CBF_CONFIGS}/sys_params/load_dish_config.json"

    tmc_central_node, tmc_subarray = tmc

    with open(DISH_CONFIG_FILE, encoding="utf-8") as f:
        dish_config_json = json.load(f)

    dish_config_json["tm_data_sources"][
        0
    ] = "car://gitlab.com/ska-telescope/ska-telmodel-data?0.1.0-rc-mid-itf#tmdata"
    dish_config_json["tm_data_filepath"] = (
        "instrument/ska1_mid_itf/ska-mid-cbf-system-parameters.json"
    )
    print(f"dish_config_json file contents: \n{dish_config_json}")

    tmc_central_node.LoadDishCfg(json.dumps(dish_config_json))

    wait_until(tmc_central_node, "isDishVccConfigSet", True, EventType.CHANGE_EVENT, 3)

    assert tmc_central_node.isDishVccConfigSet == True


@when("I configure it for a scan")
def _():
    """I configure it for a scan."""
    print("Running when")


@then("the telescope is ready for scan")
def _():
    """the telescope is ready for scan."""
    print("Running then")
