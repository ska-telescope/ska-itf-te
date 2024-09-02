"""Configure scan via TMC feature tests."""

import os
from time import localtime, strftime
from queue import Queue, Empty
import enum
import json
import pytest
from pytest_bdd import given, scenario, then, when
from tango import DeviceProxy, EventType, DevState

from ska_control_model import ObsState


# TODO: Remove usage of globals like this

CLUSTER_DOMAIN = "miditf.internal.skao.int"
SUT_NAMESPACE = os.getenv("KUBE_NAMESPACE")
DATA_DIR = "tests/integration/resources/data"
TMC_CONFIGS = f"{DATA_DIR}/tmc"


@pytest.fixture
def receptor_ids():
    receptors = ["SKA001", "SKA036"]
    return receptors


class DishMode(enum.IntEnum):
    STARTUP = 0
    SHUTDOWN = 1
    STANDBY_LP = 2
    STANDBY_FP = 3
    MAINTENANCE = 4
    STOW = 5
    CONFIG = 6
    OPERATE = 7
    UNKNOWN = 8


def wait_until(device_proxy, attr_name, desired_value, event_type, n_events=2, timeout=10):
    event_queue = Queue()

    device_proxy.subscribe_event(attr_name, event_type, lambda event: event_queue.put(event))

    try:
        for _ in range(n_events):
            event = event_queue.get(timeout=timeout)
            print(f"Received event: {event}")
            assert event.err == False, "Event error"

            value = event.attr_value.value
            if value == desired_value:
                print(
                    f"Attribute {attr_name} changed to the following desired value: {desired_value}"
                )
                break
    except Empty:
        pytest.fail(
            f"Attribute {attr_name} change event did not occur within timeout period of {timeout}s"
        )


@scenario("features/tmc_configure_scan.feature", "Configure scan via TMC on 1 subarray in mid")
def test_configure_scan_via_tmc_on_1_subarray_in_mid():
    """Configure scan via TMC on 1 subarray in mid."""


@pytest.fixture(autouse=True, scope="session")
def set_context():
    CURRENT_TANGO_HOST = os.environ.get("TANGO_HOST")
    CURRENT_TZ = os.environ.get("TZ")

    TANGO_HOST = f"tango-databaseds.{SUT_NAMESPACE}.svc.{CLUSTER_DOMAIN}:10000"
    os.environ["TANGO_HOST"] = TANGO_HOST
    os.environ["TZ"] = "Africa/Johannesburg"

    yield

    if CURRENT_TANGO_HOST:
        os.environ["TANGO_HOST"] = CURRENT_TANGO_HOST

    if CURRENT_TZ:
        os.environ["TZ"] = CURRENT_TZ


@given("a TMC configured with 1 subarray", target_fixture="tmc")
def _():
    """a TMC configured with 1 subarray."""
    print("Getting TMC DeviceProxies")

    tmc_central_node = DeviceProxy("ska_mid/tm_central/central_node")
    tmc_subarray = DeviceProxy("ska_mid/tm_subarray_node/1")
    tmc_csp_master = DeviceProxy("ska_mid/tm_leaf_node/csp_master")
    tmc_csp_subarray = DeviceProxy("ska_mid/tm_leaf_node/csp_subarray01")
    sdp_subarray_leaf_node = DeviceProxy("ska_mid/tm_leaf_node/sdp_subarray01")
    csp_subarray_leaf_node = DeviceProxy("ska_mid/tm_leaf_node/csp_subarray01")

    assert tmc_central_node.ping() > 0
    assert tmc_subarray.ping() > 0
    assert tmc_csp_master.ping() > 0
    assert tmc_csp_subarray.ping() > 0
    assert sdp_subarray_leaf_node.ping() > 0
    assert csp_subarray_leaf_node.ping() > 0

    return (
        tmc_central_node,
        tmc_subarray,
        tmc_csp_master,
        tmc_csp_subarray,
        sdp_subarray_leaf_node,
        csp_subarray_leaf_node,
    )


@given("a CSP in adminMode online", target_fixture="csp")
def _():
    """a CSP in adminMode online"""
    print("Getting CSP DeviceProxy and setting online")

    csp_control = DeviceProxy("mid-csp/control/0")
    assert csp_control.ping() > 0

    csp_control.adminMode = 0


@given("a CBF", target_fixture="cbf")
def _():
    """a CBF"""

    cbf_controller = DeviceProxy("mid_csp_cbf/sub_elt/controller")
    cbf_subarray = DeviceProxy("mid_csp_cbf/sub_elt/subarray_01")
    cbf_fspcorrsubarray = DeviceProxy("mid_csp_cbf/fspcorrsubarray/01_01")
    assert cbf_controller.ping() > 0
    assert cbf_subarray.ping() > 0
    assert cbf_fspcorrsubarray.ping() > 0

    return cbf_controller, cbf_subarray, cbf_fspcorrsubarray


@given("dishes d0001 and d0036", target_fixture="dishes")
def _():
    """dishes d0001 and d0036"""

    dish_leaf_node_ska001 = DeviceProxy("ska_mid/tm_leaf_node/d0001")
    dish_leaf_node_ska036 = DeviceProxy("ska_mid/tm_leaf_node/d0036")
    assert dish_leaf_node_ska001.ping() > 0
    assert dish_leaf_node_ska036.ping() > 0

    return dish_leaf_node_ska001, dish_leaf_node_ska036


@given("a telescope in the ON state")
def _(tmc, csp, cbf, dishes, receptor_ids):
    """I turn the telescope ON."""
    print("Turning telescope ON")

    (
        tmc_central_node,
        tmc_subarray,
        tmc_csp_master,
        tmc_csp_subarray,
        sdp_subarray_leaf_node,
        _,
    ) = tmc
    _, _, cbf_fspcorrsubarray = cbf
    dish_leaf_node_ska001, dish_leaf_node_ska036 = dishes
    RECEPTORS = receptor_ids

    # Load DishVCCConfig
    CBF_CONFIGS = f"{DATA_DIR}/cbf"
    DISH_CONFIG_FILE = f"{CBF_CONFIGS}/sys_params/load_dish_config.json"

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

    wait_until(tmc_central_node, "isDishVccConfigSet", True, EventType.CHANGE_EVENT, 20)

    assert tmc_central_node.isDishVccConfigSet == True

    dish_vcc_config = json.loads(tmc_csp_master.dishVccConfig)

    for receptor in RECEPTORS:
        assert dish_vcc_config["dish_parameters"][receptor]["k"] == 1

    # Turn ON the telescope
    assert cbf_fspcorrsubarray.obsstate == ObsState.IDLE
    assert dish_leaf_node_ska001.dishMode == DishMode.STANDBY_LP
    assert dish_leaf_node_ska036.dishMode == DishMode.STANDBY_LP
    assert tmc_subarray.obsState == ObsState.EMPTY
    assert tmc_csp_subarray.cspSubarrayObsState == ObsState.EMPTY
    assert sdp_subarray_leaf_node.sdpSubarrayObsState == ObsState.EMPTY

    tmc_central_node.TelescopeOn()
    wait_until(tmc_central_node, "telescopeState", DevState.ON, EventType.CHANGE_EVENT, 120)

    assert tmc_central_node.telescopeState == DevState.ON
    assert dish_leaf_node_ska001.dishMode == DishMode.STANDBY_FP
    dish_leaf_node_ska036.dishMode == DishMode.STANDBY_FP


@when("I assign resources")
def _(tmc, cbf, receptor_ids):
    """I assign resources."""
    print("Assigning resources")

    _, tmc_subarray, _, _, sdp_subarray_leaf_node, csp_subarray_leaf_node = tmc
    _, cbf_subarray, _ = cbf

    ASSIGN_RESOURCES_FILE = f"{TMC_CONFIGS}/assign_resources.json"
    KAFKA_PORT = 9092
    KAFKA_SERVICE_NAME = "ska-sdp-kafka"
    KAFKA_ENDPOINT = f"{KAFKA_SERVICE_NAME}.{SUT_NAMESPACE}.svc.{CLUSTER_DOMAIN}:{KAFKA_PORT}"
    RECEPTORS = receptor_ids

    time_now = localtime()
    date = strftime("%Y%m%d", time_now)
    time_now = strftime("%H%M%S", time_now)
    eb_id = f"eb-test-{date}-{time_now}"
    pb_id = f"pb-test-{date}-{time_now}"

    with open(ASSIGN_RESOURCES_FILE, encoding="utf-8") as f:
        assign_resources_json = json.load(f)
        assign_resources_json["dish"]["receptor_ids"] = RECEPTORS
        assign_resources_json["sdp"]["resources"]["receptors"] = RECEPTORS
        assign_resources_json["sdp"]["processing_blocks"][0]["parameters"][
            "queue_connector_configuration"
        ]["exchanges"][0]["source"]["servers"] = KAFKA_ENDPOINT
        assign_resources_json["sdp"]["processing_blocks"][0]["parameters"]["extra_helm_values"][
            "receiver"
        ]["options"]["reception"][
            "stats_receiver_kafka_config"
        ] = f"{KAFKA_ENDPOINT}:json_workflow_state"
        assign_resources_json["sdp"]["execution_block"]["eb_id"] = eb_id
        assign_resources_json["sdp"]["processing_blocks"][0]["pb_id"] = pb_id

    print(f"PB ID: {pb_id}, EB ID: {eb_id}")

    tmc_subarray.AssignResources(json.dumps(assign_resources_json))
    wait_until(tmc_subarray, "obsState", ObsState.IDLE, EventType.CHANGE_EVENT, 20)
    wait_until(cbf_subarray, "obsState", ObsState.IDLE, EventType.CHANGE_EVENT, 20)
    wait_until(
        sdp_subarray_leaf_node, "sdpSubarrayObsState", ObsState.IDLE, EventType.CHANGE_EVENT, 20
    )
    wait_until(
        csp_subarray_leaf_node, "cspSubarrayObsState", ObsState.IDLE, EventType.CHANGE_EVENT, 20
    )


@when("configure it for a scan")
def _(tmc, dishes):
    """configure it for a scan."""
    print("Configuring scan")

    _, tmc_subarray, _, _, sdp_subarray_leaf_node, csp_subarray_leaf_node = tmc
    dish_leaf_node_ska001, dish_leaf_node_ska036 = dishes
    CONFIGURE_SCAN_FILE = f"{TMC_CONFIGS}/configure_scan.json"

    with open(CONFIGURE_SCAN_FILE, encoding="utf-8") as f:
        configure_scan_json = json.load(f)

    print(json.dumps(configure_scan_json))

    tmc_subarray.Configure(json.dumps(configure_scan_json))
    wait_until(
        csp_subarray_leaf_node, "cspSubarrayObsState", ObsState.READY, EventType.CHANGE_EVENT, 10
    )
    wait_until(
        sdp_subarray_leaf_node,
        "sdpSubarrayObsState",
        ObsState.READY,
        EventType.CHANGE_EVENT,
        3,
        timeout=40,
    )
    wait_until(dish_leaf_node_ska001, "dishMode", DishMode.OPERATE, EventType.CHANGE_EVENT, 10)
    wait_until(dish_leaf_node_ska036, "dishMode", DishMode.OPERATE, EventType.CHANGE_EVENT, 10)


@then("the telescope is ready for scan")
def _():
    """the telescope is ready for scan."""
    print("Running then")
