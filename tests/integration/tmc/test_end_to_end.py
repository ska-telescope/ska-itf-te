"""Configure scan via TMC feature tests."""

import json
import logging
import os
from time import localtime, sleep, strftime
from typing import Generator, List, Tuple

import pytest
from pytest_bdd import given, parsers, scenario, then, when
from ska_control_model import ObsState
from tango import DeviceProxy, DevState

from tests.integration.tmc.conftest import CBF, CSP, TMC, Dish, wait_for_event
from utils.enums import DishMode

# TODO: Rethink usage of globals like this
CLUSTER_DOMAIN = "miditf.internal.skao.int"
SUT_NAMESPACE = "ci-ska-mid-itf-at-2586-verify-skb-606"  # os.getenv("KUBE_NAMESPACE")
DATA_DIR = "tests/integration/resources/data"
TMC_CONFIGS = f"{DATA_DIR}/tmc"
expected_k_value = 1
logger = logging.getLogger()
OVERRIDE_SCAN_DURATION = os.getenv("OVERRIDE_SCAN_DURATION")


@scenario(
    "features/tmc_end_to_end.feature",
    "End to End signal chain verification via TMC",
)
def test_e2e_via_tmc():
    """."""


@pytest.mark.hw_in_the_loop
@scenario(
    "features/tmc_end_to_end.feature",
    "End to End signal chain verification via TMC - With HW",
)
def test_e2e_via_tmc_slow():
    """."""
    global SUT_NAMESPACE

    if not (SUT_NAMESPACE := os.getenv("E2E_TEST_EXECUTION_NAMESPACE")):
        SUT_NAMESPACE = os.getenv("KUBE_NAMESPACE")


# TODO: Consider removing this e.g. read from config file or feature file
@pytest.fixture(scope="session")
def receptor_ids():
    """Fixture for generating list of receptors to be used in test.

    :return: List of receptor IDs
    :rtype: _type_
    """
    receptors = ["SKA001", "SKA036", "SKA063", "SKA100"]
    return receptors


@pytest.fixture(autouse=True, scope="session")
def set_context():
    """Fixture for configuring environment and global variables for the test.

    :yield: _
    """
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


@pytest.fixture(scope="session")
def pb_and_eb_ids() -> Tuple[str, str]:
    """Fixture for generating pb and eb ids for the scan.

    :return: pb_id and eb_id for use in the assign_resources.json
    :rtype: Tuple[str, str]
    """
    time_now = localtime()
    date = strftime("%Y%m%d", time_now)
    time_now = strftime("%H%M%S", time_now)
    eb_id = f"eb-test-{date}-{time_now}"
    pb_id = f"pb-test-{date}-{time_now}"
    return pb_id, eb_id


@pytest.fixture(scope="session")
def telescope_handlers(receptor_ids) -> Generator[Tuple[TMC, CBF, CSP, List[Dish]], None, None]:
    """Generate telescope handlers containing device proxies. Teardown telescope on completion.

    :param receptor_ids: _description_
    :type receptor_ids: _type_
    :yield: _description_
    :rtype: Generator[Tuple[TMC, CBF, CSP, List[Dish]], None, None]
    """
    logger.info(f"Using the following SUT Tango host: {os.getenv('TANGO_HOST')}")
    RECEPTORS = receptor_ids
    tmc = TMC()
    cbf = CBF()
    csp = CSP()
    dishes = [Dish(SUT_NAMESPACE, receptor) for receptor in RECEPTORS]

    yield tmc, cbf, csp, dishes
    tmc.tear_down()


@given("an SUT deployment with 1 subarray")
def _(telescope_handlers):
    """Trigger instantiation of telescope handler objects.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    """
    _, _, csp, _ = telescope_handlers
    csp_control = csp.control
    csp_subarray = csp.subarray
    SIM_MODE = os.getenv("SIM_MODE", "false").lower()

    if (csp_control.adminMode == 0) or (csp_subarray.adminMode == 0):
        # CSP should be OFFLINE when CBF Sim mode is set
        csp_control.adminMode = 1
        csp_subarray.adminMode = 1
        wait_for_event(csp_control, "adminMode", 1)
        wait_for_event(csp_subarray, "adminMode", 1)
        sleep(4)

    if SIM_MODE in ["false", "0", ""]:
        csp.set_cbf_simulation_mode(False)
    elif SIM_MODE in ["true", "1"]:
        csp.set_cbf_simulation_mode(True)


@given("CSP in adminMode online", target_fixture="csp")
def _(telescope_handlers):
    """Set CSP adminMode to Online after handling simulation/hw_in_the_loop.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    """
    logger.info("Getting CSP DeviceProxy and setting online")

    _, _, csp, _ = telescope_handlers
    csp_control = csp.control
    csp_subarray = csp.subarray

    assert csp_control.ping() > 0

    csp_control.commandTimeout = 99  # TO BE REMOVED once CSP-CBF LRC's are implemented
    csp_control.commandTimeout = 99  # TO BE REMOVED once CSP-CBF LRC's are implemented
    csp_control.adminMode = 0
    csp_subarray.adminMode = 0
    wait_for_event(csp_control, "adminMode", 0)
    wait_for_event(csp_subarray, "adminMode", 0)
    sleep(5)  # TODO: Find out exactly why this is needed

    logger.info(
        f"CSP adminMode is: {csp_control.adminMode},"
        f" CBF Simulation mode is: {csp_control.cbfSimulationMode}"
    )


@when("I turn ON the telescope")
def _(telescope_handlers, receptor_ids):
    """Turn the telescope ON.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    :param receptor_ids: _description_
    :type receptor_ids: _type_
    """
    logger.info("Turning telescope ON")
    RECEPTORS = receptor_ids

    tmc, cbf, _, _ = telescope_handlers

    tmc_central_node = tmc.central_node
    tmc_subarray_node = tmc.subarray_node
    sdp_subarray_leaf_node = tmc.sdp_subarray_leaf_node
    csp_subarray_leaf_node = tmc.csp_subarray_leaf_node
    cbf_fspcorrsubarray = cbf.fspcorrsubarray

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
    logger.debug(f"dish_config_json file contents: \n{dish_config_json}")

    k_value_correct = 1
    if tmc_central_node.isDishVccConfigSet:
        dish_vcc_config = json.loads(tmc.csp_master_leaf_node.dishVccConfig)
        for receptor in RECEPTORS:
            if dish_vcc_config["dish_parameters"][receptor]["k"] != 1:
                k_value_correct = 0
                break

    if (not tmc_central_node.isDishVccConfigSet) or (not k_value_correct):
        tmc_central_node.LoadDishCfg(json.dumps(dish_config_json))
        wait_for_event(tmc_central_node, "isDishVccConfigSet", True)

    dish_vcc_config = json.loads(tmc.csp_master_leaf_node.dishVccConfig)

    for receptor in RECEPTORS:
        assert dish_vcc_config["dish_parameters"][receptor]["k"] == expected_k_value

    # Turn ON the telescope
    assert cbf_fspcorrsubarray.obsstate == ObsState.IDLE
    for receptor in RECEPTORS:
        assert tmc.get_dish_leaf_node_dp(receptor).dishMode == DishMode.STANDBY_LP
    assert tmc_subarray_node.obsState == ObsState.EMPTY
    assert csp_subarray_leaf_node.cspSubarrayObsState == ObsState.EMPTY
    assert sdp_subarray_leaf_node.sdpSubarrayObsState == ObsState.EMPTY

    tmc_central_node.TelescopeOn()
    wait_for_event(tmc_central_node, "telescopeState", DevState.ON)
    sleep(120)  # TODO: Remove once we know how to properly check that the CBF is ON

    assert tmc_central_node.telescopeState == DevState.ON
    for receptor in RECEPTORS:
        assert tmc.get_dish_leaf_node_dp(receptor).dishMode == DishMode.STANDBY_FP


@when("I assign resources")
def _(telescope_handlers, receptor_ids, pb_and_eb_ids):
    """Assign resources via TMC.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    :param receptor_ids: _description_
    :type receptor_ids: _type_
    :param pb_and_eb_ids: _description_
    :type pb_and_eb_ids: _type_
    """
    logger.info("Assigning resources")

    tmc, cbf, _, _ = telescope_handlers
    pb_id, eb_id = pb_and_eb_ids

    tmc_subarray_node = tmc.subarray_node
    sdp_subarray_leaf_node = tmc.sdp_subarray_leaf_node
    csp_subarray_leaf_node = tmc.csp_subarray_leaf_node
    cbf_subarray = cbf.subarray

    ASSIGN_RESOURCES_FILE = f"{TMC_CONFIGS}/assign_resources.json"
    RECEPTORS = receptor_ids

    with open(ASSIGN_RESOURCES_FILE, encoding="utf-8") as f:
        assign_resources_json = json.load(f)
        assign_resources_json["dish"]["receptor_ids"] = RECEPTORS
        assign_resources_json["sdp"]["resources"]["receptors"] = RECEPTORS
        assign_resources_json["sdp"]["execution_block"]["eb_id"] = eb_id
        assign_resources_json["sdp"]["processing_blocks"][0]["pb_id"] = pb_id

        # TODO: Include once band param calculation methods are centralised
        # band_params = generate_fsp.generate_band_params(SCAN_BAND)
        # # Add in Frequency bounds and the channel count
        # assign_resources_json["sdp"]["execution_block"]["channels"][0]["spectral_windows"][0][
        #     "freq_min"
        # ] = band_params["start_freq"]
        # assign_resources_json["sdp"]["execution_block"]["channels"][0]["spectral_windows"][0][
        #     "freq_max"
        # ] = f_limits["freq_max"]
        # assign_resources_json["sdp"]["execution_block"]["channels"][0]["spectral_windows"][0][
        #     "count"
        # ] = band_params["channel_count"]

    logger.info(f"PB ID: {pb_id}, EB ID: {eb_id}")

    tmc.subarray_node.AssignResources(json.dumps(assign_resources_json))
    wait_for_event(cbf_subarray, "obsState", ObsState.IDLE)
    wait_for_event(sdp_subarray_leaf_node, "sdpSubarrayObsState", ObsState.IDLE)
    wait_for_event(csp_subarray_leaf_node, "cspSubarrayObsState", ObsState.IDLE)
    wait_for_event(tmc_subarray_node, "obsState", ObsState.IDLE)
    sleep(20) # TODO: Bring in vis-receive check method


@when("configure it for a scan")
def _(telescope_handlers, receptor_ids):
    """Configure scan via TMC.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    :param receptor_ids: _description_
    :type receptor_ids: _type_
    """
    logger.info("Configuring scan")

    tmc, _, _, dishes = telescope_handlers
    RECEPTORS = receptor_ids

    CONFIGURE_SCAN_FILE = f"{TMC_CONFIGS}/configure_scan.json"

    with open(CONFIGURE_SCAN_FILE, encoding="utf-8") as f:
        configure_scan_json = json.load(f)

    logger.debug(json.dumps(configure_scan_json))

    # TODO: Remove once TMC correctly checks command completion using LRC unique_ids
    for dish in dishes:
        dish.get_dish_manager_proxy().ConfigureBand1(True)
        dish_tango_host = dish.get_dish_tango_host()
        spfrx_controller = DeviceProxy(
            f"{dish_tango_host}/{dish.dish_id.lower()}/spfrxpu/controller"
        )
        wait_for_event(spfrx_controller, "configuredBand", 1)
    sleep(2)

    tmc.subarray_node.Configure(json.dumps(configure_scan_json))
    wait_for_event(tmc.csp_subarray_leaf_node, "cspSubarrayObsState", ObsState.READY)
    wait_for_event(tmc.sdp_subarray_leaf_node, "sdpSubarrayObsState", ObsState.READY)
    for receptor in RECEPTORS:
        wait_for_event(tmc.get_dish_leaf_node_dp(receptor), "dishMode", DishMode.OPERATE)
    wait_for_event(tmc.subarray_node, "obsState", ObsState.READY)


@when(
    parsers.cfparse("I start a scan for {scan_time:Number} seconds", extra_types={"Number": float})
)
def _(telescope_handlers, scan_time):
    """Block for scan_time while telescope is in SCANNING state.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    :param scan_time: _description_
    :type scan_time: _type_
    """
    logger.info("Scanning")

    tmc, _, _, _ = telescope_handlers

    SCAN_FILE = f"{TMC_CONFIGS}/scan.json"
    with open(SCAN_FILE, encoding="utf-8") as f:
        scan_json = f.read()

    if OVERRIDE_SCAN_DURATION:
        scan_time = int(OVERRIDE_SCAN_DURATION)

    tmc.subarray_node.Scan(scan_json)
    wait_for_event(tmc.sdp_subarray_leaf_node, "sdpSubarrayObsState", ObsState.SCANNING)
    wait_for_event(tmc.csp_subarray_leaf_node, "cspSubarrayObsState", ObsState.SCANNING)
    wait_for_event(tmc.subarray_node, "obsState", ObsState.SCANNING)
    logger.info(f"Scanning for {scan_time} seconds")
    sleep(scan_time)


@when("I end the scan")
def _(telescope_handlers):
    """End scan via TMC.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    """
    logger.info("Ending the scan")

    tmc, _, _, _ = telescope_handlers

    tmc.subarray_node.EndScan()

    wait_for_event(tmc.sdp_subarray_leaf_node, "sdpSubarrayObsState", ObsState.READY)
    wait_for_event(tmc.csp_subarray_leaf_node, "cspSubarrayObsState", ObsState.READY)
    wait_for_event(tmc.subarray_node, "obsState", ObsState.READY)


@when("I end the observation")
def _(telescope_handlers):
    """End observation via TMC.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    """
    logger.info("Ending the observation")

    tmc, _, _, _ = telescope_handlers

    tmc_subarray_node = tmc.subarray_node
    sdp_subarray_leaf_node = tmc.sdp_subarray_leaf_node
    csp_subarray_leaf_node = tmc.csp_subarray_leaf_node

    tmc.subarray_node.End()
    wait_for_event(sdp_subarray_leaf_node, "sdpSubarrayObsState", ObsState.IDLE)
    wait_for_event(csp_subarray_leaf_node, "cspSubarrayObsState", ObsState.IDLE)
    wait_for_event(tmc_subarray_node, "obsState", ObsState.IDLE)


@when("I release resources")
def _(telescope_handlers):
    """Release resources via TMC.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    """
    logger.info("Releasing resources")

    tmc, _, _, _ = telescope_handlers

    tmc_subarray_node = tmc.subarray_node
    sdp_subarray_leaf_node = tmc.sdp_subarray_leaf_node
    csp_subarray_leaf_node = tmc.csp_subarray_leaf_node

    tmc_subarray_node.ReleaseAllResources()
    wait_for_event(sdp_subarray_leaf_node, "sdpSubarrayObsState", ObsState.EMPTY)
    wait_for_event(csp_subarray_leaf_node, "cspSubarrayObsState", ObsState.EMPTY)
    wait_for_event(tmc_subarray_node, "obsState", ObsState.EMPTY)


@when("I turn OFF the telescope")
def _(telescope_handlers, receptor_ids):
    """Turn the telescope OFF via TMC.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    :param receptor_ids: _description_
    :type receptor_ids: _type_
    """
    logger.info("Turning OFF the telescope")

    tmc, _, _, _ = telescope_handlers
    RECEPTORS = receptor_ids

    tmc_central_node = tmc.central_node

    tmc_central_node.TelescopeOff()

    for receptor in RECEPTORS:
        wait_for_event(tmc.get_dish_leaf_node_dp(receptor), "dishMode", DishMode.STANDBY_LP)

    wait_for_event(tmc_central_node, "telescopeState", DevState.OFF)


@then("the telescope is in the OFF state")
def _(telescope_handlers):
    """Check that the telescope is in the OFF state.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    """
    tmc, _, _, _ = telescope_handlers

    tmc_central_node = tmc.central_node

    assert tmc_central_node.telescopeState in [DevState.OFF, DevState.UNKNOWN]


@then("the respective dataproducts are available on the DPD")
def _(pb_and_eb_ids):
    """Check that the respective dataproducts are available on the DPD via the dataproducts API.

    :param pb_and_eb_ids: _description_
    :type pb_and_eb_ids: _type_
    """
    # TODO: Implement
    pb_id, eb_id = pb_and_eb_ids

    assert True
