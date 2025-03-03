"""."""

import json
import logging
import os
import pathlib
import sys
from queue import Empty, Queue
from time import localtime, sleep, strftime, time
from typing import Any, Generator, List, Tuple

import pytest
from pytest_bdd import given, parsers, then, when
from ska_control_model import ObsState
from tango import DeviceProxy, DevState, EventType

from scripts.sequence_diagrammer.generate_sequence_diagram import sequenceDiagrammer
from utils.enums import DishMode

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), ".jupyter-notebooks")))
from src.notebook_tools import generate_fsp  # noqa: E402

logger = logging.getLogger()


class TMC:
    """Helper class containing TMC specific details such as device names and proxies."""

    def __init__(self):
        """."""
        self.central_node = DeviceProxy("ska_mid/tm_central/central_node")
        self.subarray_node = DeviceProxy("ska_mid/tm_subarray_node/1")
        self.sdp_subarray_leaf_node = DeviceProxy("ska_mid/tm_leaf_node/sdp_subarray01")
        self.csp_master_leaf_node = DeviceProxy("ska_mid/tm_leaf_node/csp_master")
        self.csp_subarray_leaf_node = DeviceProxy("ska_mid/tm_leaf_node/csp_subarray01")

        proxies = [
            self.central_node,
            self.subarray_node,
            self.sdp_subarray_leaf_node,
            self.csp_master_leaf_node,
            self.csp_subarray_leaf_node,
        ]

        self.check_proxies(proxies)

    def get_subarray_node_dp(self, subarray_id) -> DeviceProxy:
        """Get device proxy for a specific subarray node.

        :param subarray_id: _description_
        :type subarray_id: _type_
        :return: _description_
        :rtype: DeviceProxy
        """
        return DeviceProxy(f"ska_mid/tm_subarray_node/{subarray_id}")

    def get_dish_leaf_node_dp(self, dish_id) -> DeviceProxy:
        """Get device proxy for a specific dish leaf node.

        :param dish_id: _description_
        :type dish_id: _type_
        :return: _description_
        :rtype: DeviceProxy
        """
        dish_number = int(dish_id.lower().split("ska", maxsplit=1)[1])
        dp = DeviceProxy(f"ska_mid/tm_leaf_node/d{dish_number:04}")
        assert dp.ping() > 0
        return dp

    def tear_down(self):
        """Tear down the telescope. Bring back to the OFF state."""
        pass

    def check_proxies(self, proxies):
        """Ping device proxies to confirm connectivity.

        :param proxies: _description_
        :type proxies: _type_
        """
        for proxy in proxies:
            assert proxy.ping() > 0


class CBF:
    """Helper class containing CBF specific details such as device names and proxies."""

    def __init__(self):
        """."""
        self.controller = DeviceProxy("mid_csp_cbf/sub_elt/controller")
        self.subarray = DeviceProxy("mid_csp_cbf/sub_elt/subarray_01")
        self.fspcorrsubarray = DeviceProxy("mid_csp_cbf/fspcorrsubarray/01_01")


class CSP:
    """Helper class containing CSP specific details such as device names and proxies."""

    def __init__(self):
        """."""
        self.control = DeviceProxy("mid-csp/control/0")
        self.subarray = DeviceProxy("mid-csp/subarray/01")

        proxies = [self.control, self.subarray]

        self.check_proxies(proxies)

        self.control.commandTimeout = 99  # TO BE REMOVED once CSP-CBF LRC's are implemented
        self.subarray.commandTimeout = 99  # TO BE REMOVED once CSP-CBF LRC's are implemented

    def check_proxies(self, proxies):
        """Ping device proxies to confirm connectivity.

        :param proxies: _description_
        :type proxies: _type_
        """
        for proxy in proxies:
            assert proxy.ping() > 0

    def set_cbf_simulation_mode(self, simulation_mode: bool):
        """Set CBF simulation mode.

        :param simulation_mode: _description_
        :type simulation_mode: bool
        """
        if simulation_mode:
            self.control.cbfSimulationMode = 1
            sleep(5)  # TODO: Enable use of events to check simulationmode
            # wait_for_event(self.control, "cbfSimulationMode", 1)
        else:
            self.control.cbfSimulationMode = 0
            sleep(5)  # TODO: Enable use of events to check simulationmode
            # wait_for_event(self.control, "cbfSimulationMode", 1)


class Dish:
    """Helper class containing Dish specific details."""

    def __init__(self, sut_namespace: str, dish_id: str):
        """.

        :param sut_namespace: Namespace into which the SUT has been deployed
        :type sut_namespace: str
        :param dish_id: Dish ID with the SKA prefix e.g. SKA001
        :type dish_id: str
        """
        self.sut_namespace = sut_namespace
        self.dish_id = dish_id
        self.dish_tango_host = self.get_dish_tango_host()

    def get_dish_manager_proxy(self) -> DeviceProxy:
        """.

        :return: _description_
        :rtype: DeviceProxy
        """
        dish_number = int(self.dish_id.lower().split("ska", maxsplit=1)[1])
        dp = DeviceProxy(f"{self.dish_tango_host}/mid-dish/dish-manager/ska{dish_number:03}")
        assert dp.ping() > 0
        return dp

    def get_dish_namespace(self) -> str:
        """.

        :return: _description_
        :rtype: str
        """
        if self.sut_namespace in ["staging", "integration"]:
            return f"{self.sut_namespace}-dish-lmc-{str.lower(self.dish_id)}"
        else:
            return f"ci-dish-lmc-{str.lower(self.dish_id)}-{self.sut_namespace[15:]}"

    def get_dish_tango_host(self):
        """.

        :return: _description_
        :rtype: _type_
        """
        dish_namespace = self.get_dish_namespace()
        return f"tango-databaseds.{dish_namespace}.svc.miditf.internal.skao.int:10000"

    def check_proxies(self, proxies):
        """Ping device proxies to confirm connectivity.

        :param proxies: _description_
        :type proxies: _type_
        """
        for proxy in proxies:
            assert proxy.ping() > 0


class EventWaitTimeout(Exception):
    """Exception raised when an event does not occur within a specified timeout."""


def wait_for_event(
    device_proxy: DeviceProxy,
    attr_name: str,
    desired_value: Any,
    event_type: EventType = EventType.CHANGE_EVENT,
    timeout: float = 150.0,
    print_event_details: bool = False,
) -> bool:
    """Wait for a specific type of attribute event to occur.

    Waits and checks changes against desired_value.

    :param device_proxy: Device proxy to be used for event subscription
    :type device_proxy: DeviceProxy
    :param attr_name: Attribute of interest
    :type attr_name: str
    :param desired_value: Expected value for attribute specified with attr_name
    :type desired_value: Any
    :param event_type: Tango event type to wait for, defaults to EventType.CHANGE_EVENT
    :type event_type: EventType
    :param timeout: Maximum period in [s] to wait for desired event, defaults to 150.0
    :type timeout: float
    :param print_event_details: Toggle printing of event data structure, defaults to False
    :type print_event_details: bool
    :raises EventWaitTimeout: _description_
    :return: Success or failure flag indicating whether the attribute changed as desired or not
    :rtype: bool
    """
    # TODO: Report attribute name instead of value where possible

    result = False

    event_queue = Queue()

    event_id = device_proxy.subscribe_event(attr_name, event_type, event_queue.put)
    attr_val_name = desired_value
    try:
        attr_val_name = desired_value.name
    except AttributeError:
        # Accept failure to obtain name
        pass

    time_start = time()
    while (time() - time_start) < timeout:
        if not event_queue.empty():
            try:
                event = event_queue.get(timeout=2)
                if print_event_details:
                    logger.debug(f"Received event: {event}")
                assert not event.err, "Event error"

                value = event.attr_value.value
                if value == desired_value:
                    logger.info(
                        f"Device {device_proxy.name()} attribute {attr_name} changed "
                        f"to the following desired value: {attr_val_name}"
                    )
                    result = True
                    break
            except Empty:
                logger.error("Event queue empty")

    device_proxy.unsubscribe_event(event_id)

    if not result:
        logger.error(
            f"Desired event {device_proxy.name()} {attr_name}={attr_val_name}"
            f" did not occur within the timeout period of {timeout}s"
        )
        raise EventWaitTimeout(
            f"Desired event {device_proxy.name()} {attr_name}={attr_val_name}"
            f" did not occur within the timeout period of {timeout}s"
        )
    return result


# TODO: Consider removing this e.g. read from config file or feature file
@pytest.fixture(scope="session")
def settings():
    """Fixture for generating settings to be used in the test.

    :return: _description_
    :rtype: _type_
    """
    settings = {}
    settings["cluster_domain"] = "miditf.internal.skao.int"
    settings["SUT_namespace"] = os.getenv("KUBE_NAMESPACE")
    settings["data_dir"] = ".jupyter-notebooks/data/mid_telescope"
    settings["TMC_configs"] = f"{settings['data_dir']}/tmc"
    settings["expected_k_value"] = 1
    settings["override_scan_duration"] = os.getenv("OVERRIDE_SCAN_DURATION")
    settings["override_scan_band"] = os.getenv("OVERRIDE_SCAN_BAND")
    settings["integration_factor"] = os.getenv("INTEGRATION_FACTOR")
    settings["sim_mode"] = os.getenv("SIM_MODE", "false").lower()
    settings["generate_sequence_diagram"] = (
        os.getenv("GENERATE_SEQUENCE_DIAGRAM", "false").lower() == "true"
    )

    return settings


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
def set_context(settings):
    """Fixture for configuring environment and global variables for the test.

    :param settings: _description_
    :type settings: _type_
    :yield: _
    """
    CURRENT_TANGO_HOST = os.environ.get("TANGO_HOST")
    CURRENT_TZ = os.environ.get("TZ")

    TANGO_HOST = (
        f"tango-databaseds.{settings['SUT_namespace']}.svc.{settings['cluster_domain']}:10000"
    )
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
def telescope_handlers(
    receptor_ids, settings
) -> Generator[Tuple[TMC, CBF, CSP, List[Dish]], None, None]:
    """Generate telescope handlers containing device proxies. Teardown telescope on completion.

    :param receptor_ids: _description_
    :type settings: _type_
    :type receptor_ids: _type_
    :yield: _description_
    :rtype: Generator[Tuple[TMC, CBF, CSP, List[Dish]], None, None]
    """
    logger.info(f"Using the following SUT Tango host: {os.getenv('TANGO_HOST')}")
    RECEPTORS = receptor_ids
    tmc = TMC()
    cbf = CBF()
    csp = CSP()
    dishes = [Dish(settings["SUT_namespace"], receptor) for receptor in RECEPTORS]

    yield tmc, cbf, csp, dishes
    tmc.tear_down()


@pytest.fixture
def sequence_diagrammer(settings):
    """Create a fresh sequence diagrammer instance and ensure it cleans up.

    This fixture initialises a new instance of the sequence diagrammer
    for tracking events during the test. It ensures that event tracking
    stops and the sequence diagram is generated when the test completes.

    :param settings: test settings
    :type settings: dict[str]
    :yield: An instance of sequenceDiagrammer for tracking events.
    :rtype: sequenceDiagrammer
    """
    sequence_diagrammer = sequenceDiagrammer(settings["SUT_namespace"])

    try:
        yield sequence_diagrammer  # Provide instance to test
    finally:
        if settings["generate_sequence_diagram"]:
            logger.info("Generating puml diagram")
            sequence_diagrammer.stop_tracking_and_generate_diagram()  # Cleanup after test
        else:
            pathlib.Path(sequence_diagrammer.get_puml_filename()).unlink(missing_ok=True)
            logger.info("Sequence diagram generation correctly skipped")


@given("an SUT deployment with 1 subarray")
def _(telescope_handlers):
    """Trigger instantiation of telescope handler objects.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    """
    pass


@given("a sequence diagrammer has optionally started listeing for events")
def _(sequence_diagrammer, settings):
    """Start listening for tango events and register test finaliser.

    This step initialises the sequence diagrammer and starts listening for
    Tango events if the GENERATE_SEQUENCE_DIAGRAM flag is enabled.
    The events captured during the test will be used to generate a sequence
    diagram at the end of the test.

    :param sequence_diagrammer: An instance of sequenceDiagrammer that manages
                                event tracking and diagram generation.
    :type sequence_diagrammer: sequenceDiagrammer
    :param settings: test settings
    :type settings: dict[str]
    """
    if settings["generate_sequence_diagram"]:
        logger.info("Starting event listening for puml diagram")
        sequence_diagrammer.setup()
        sequence_diagrammer.start_tracking_events()
    else:
        logger.info("Skipping sequence diagram generation")


@given("CSP in adminMode online", target_fixture="csp")
def _(telescope_handlers, settings):
    """Set CSP adminMode to Online after handling simulation/hw_in_the_loop.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    :param settings: _description_
    :type settings: _type_
    """
    logger.info("Setting CSP adminmode")

    _, _, csp, _ = telescope_handlers
    csp_control = csp.control

    assert csp_control.ping() > 0

    sim_mode = settings["sim_mode"]

    if sim_mode in ["false", "0", ""]:
        sim_mode = False
    elif sim_mode in ["true", "1"]:
        sim_mode = True
    else:
        logging.error("SIM_MODE is invalid")
        pytest.fail("SIM_MODE not correctly specified")

    # reset_csp_adminmode = (sim_mode != csp_control.cbfSimulationMode) and (
    #     (csp_control.adminMode == 0)
    # )

    # # CSP should be OFFLINE when CBF Sim mode is set
    # if reset_csp_adminmode:
    csp_control.adminMode = 1
    wait_for_event(csp_control, "adminMode", 1)
    sleep(8)

    if not sim_mode:
        csp.set_cbf_simulation_mode(False)
    elif sim_mode:
        csp.set_cbf_simulation_mode(True)

    csp_control.commandTimeout = 99  # TO BE REMOVED once CSP-CBF LRC's are implemented
    csp_control.commandTimeout = 99  # TO BE REMOVED once CSP-CBF LRC's are implemented

    csp_control.adminMode = 0
    wait_for_event(csp_control, "adminMode", 0)
    sleep(15)  # TODO: Find out exactly why this is needed

    logger.info(
        f"CSP adminMode is: {csp_control.adminMode},"
        f" CBF Simulation mode is: {csp_control.cbfSimulationMode}"
    )


@when("I turn ON the telescope")
def _(telescope_handlers, receptor_ids, settings):
    """Turn the telescope ON.

    :param telescope_handlers: _description_
    :type settings: _type_
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
    CBF_CONFIGS = f"{settings['data_dir']}/cbf"
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
        sleep(5)

    dish_vcc_config = json.loads(tmc.csp_master_leaf_node.dishVccConfig)

    for receptor in RECEPTORS:
        assert dish_vcc_config["dish_parameters"][receptor]["k"] == settings["expected_k_value"]

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


@when(
    parsers.cfparse(
        "I assign resources for a band {scan_band:Number} scan", extra_types={"Number": int}
    )
)
def _(telescope_handlers, receptor_ids, pb_and_eb_ids, scan_band, settings):
    """Assign resources via TMC.

    :param telescope_handlers: _description_
    :type settings: _type_
    :type telescope_handlers: _type_
    :param receptor_ids: _description_
    :type receptor_ids: _type_
    :param pb_and_eb_ids: _description_
    :type pb_and_eb_ids: _type_
    :param scan_band: _description_
    :type scan_band: _type_
    """
    logger.info("Assigning resources")

    tmc, cbf, _, _ = telescope_handlers
    pb_id, eb_id = pb_and_eb_ids

    tmc_subarray_node = tmc.subarray_node
    sdp_subarray_leaf_node = tmc.sdp_subarray_leaf_node
    csp_subarray_leaf_node = tmc.csp_subarray_leaf_node
    cbf_subarray = cbf.subarray

    ASSIGN_RESOURCES_FILE = f"{settings['TMC_configs']}/assign_resources.json"
    RECEPTORS = receptor_ids

    if settings["override_scan_band"]:
        scan_band = int(settings["override_scan_band"])

    band_params = generate_fsp.generate_band_params(scan_band)

    with open(ASSIGN_RESOURCES_FILE, encoding="utf-8") as f:
        assign_resources_json = json.load(f)
        assign_resources_json["dish"]["receptor_ids"] = RECEPTORS
        assign_resources_json["sdp"]["resources"]["receptors"] = RECEPTORS
        assign_resources_json["sdp"]["execution_block"]["eb_id"] = eb_id
        assign_resources_json["sdp"]["processing_blocks"][0]["pb_id"] = pb_id

        band_params = generate_fsp.generate_band_params(scan_band)

        # Add in Frequency bounds and the channel count
        assign_resources_json["sdp"]["execution_block"]["channels"][0]["spectral_windows"][0][
            "freq_min"
        ] = band_params["start_freq"]
        assign_resources_json["sdp"]["execution_block"]["channels"][0]["spectral_windows"][0][
            "freq_max"
        ] = band_params["end_freq"]
        assign_resources_json["sdp"]["execution_block"]["channels"][0]["spectral_windows"][0][
            "count"
        ] = band_params["channel_count"]

    logger.info(f"PB ID: {pb_id}, EB ID: {eb_id}")

    tmc.subarray_node.AssignResources(json.dumps(assign_resources_json))
    wait_for_event(cbf_subarray, "obsState", ObsState.IDLE)
    wait_for_event(sdp_subarray_leaf_node, "sdpSubarrayObsState", ObsState.IDLE)
    wait_for_event(csp_subarray_leaf_node, "cspSubarrayObsState", ObsState.IDLE)
    wait_for_event(tmc_subarray_node, "obsState", ObsState.IDLE)
    sleep(30)  # TODO: Remove sleep for vis-receive


@when(
    parsers.cfparse("configure it for a band {scan_band:Number} scan", extra_types={"Number": int})
)
def _(telescope_handlers, receptor_ids, scan_band, settings):
    """Configure scan via TMC.

    :param telescope_handlers: _description_
    :type settings: _type_
    :type telescope_handlers: _type_
    :param receptor_ids: _description_
    :type receptor_ids: _type_
    :param scan_band: _description_
    :type scan_band: _type_
    """
    if settings["override_scan_band"]:
        scan_band = int(settings["override_scan_band"])

    logger.info(f"Configuring a band {scan_band} scan")

    tmc, _, _, _ = telescope_handlers
    RECEPTORS = receptor_ids

    CONFIGURE_SCAN_FILE = f"{settings['TMC_configs']}/configure_scan.json"

    band_params = generate_fsp.generate_band_params(scan_band)
    fsp_list = [1, 2, 3, 4]

    with open(CONFIGURE_SCAN_FILE, encoding="utf-8") as f:
        configure_scan_json = json.load(f)
        configure_scan_json["dish"]["receiver_band"] = str(scan_band)
        configure_scan_json["csp"]["common"]["frequency_band"] = str(scan_band)

        configure_scan_json["csp"]["midcbf"]["correlation"]["processing_regions"][0][
            "fsp_ids"
        ] = fsp_list
        configure_scan_json["csp"]["midcbf"]["correlation"]["processing_regions"][0][
            "start_freq"
        ] = int(band_params["start_freq"])
        configure_scan_json["csp"]["midcbf"]["correlation"]["processing_regions"][0][
            "channel_count"
        ] = int(band_params["channel_count"])

        if settings["integration_factor"]:
            configure_scan_json["csp"]["midcbf"]["correlation"]["processing_regions"][0][
                "integration_factor"
            ] = int(settings["integration_factor"])

    logger.debug(json.dumps(configure_scan_json))

    tmc.subarray_node.Configure(json.dumps(configure_scan_json))
    wait_for_event(tmc.csp_subarray_leaf_node, "cspSubarrayObsState", ObsState.READY)
    wait_for_event(tmc.sdp_subarray_leaf_node, "sdpSubarrayObsState", ObsState.READY)
    for receptor in RECEPTORS:
        wait_for_event(tmc.get_dish_leaf_node_dp(receptor), "dishMode", DishMode.OPERATE)
    wait_for_event(tmc.subarray_node, "obsState", ObsState.READY)


@when(
    parsers.cfparse("I start a scan for {scan_time:Number} seconds", extra_types={"Number": float})
)
def _(telescope_handlers, scan_time, settings):
    """Block for scan_time while telescope is in SCANNING state.

    :param telescope_handlers: _description_
    :type settings: _type_
    :type telescope_handlers: _type_
    :param scan_time: _description_
    :type scan_time: _type_
    """
    logger.info("Issuing scan command")

    tmc, _, _, _ = telescope_handlers

    SCAN_FILE = f"{settings['TMC_configs']}/scan.json"
    with open(SCAN_FILE, encoding="utf-8") as f:
        scan_json = f.read()

    if settings["override_scan_duration"]:
        scan_time = int(settings["override_scan_duration"])

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


@then("the respective dataproducts are available on the DPD")
def _(pb_and_eb_ids):
    """Check that the respective dataproducts are available on the DPD via the dataproducts API.

    :param pb_and_eb_ids: _description_
    :type pb_and_eb_ids: _type_
    """
    # TODO: Implement
    pb_id, eb_id = pb_and_eb_ids

    assert True
