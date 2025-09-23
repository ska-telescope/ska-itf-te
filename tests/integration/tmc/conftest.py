"""."""

import json
import logging
import os
import pathlib
import sys
from queue import Empty, Queue
from time import localtime, sleep, strftime, time
from typing import Any, Generator, List, Tuple
from itertools import cycle

import pytest
from pytest_bdd import given, parsers, then, when
from ska_control_model import HealthState, ObsState
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
        self.central_node = DeviceProxy("mid-tmc/central-node/0")
        self.subarray_node = DeviceProxy("mid-tmc/subarray/01")
        self.sdp_subarray_leaf_node = DeviceProxy("mid-tmc/subarray-leaf-node-sdp/01")
        self.csp_master_leaf_node = DeviceProxy("mid-tmc/leaf-node-csp/0")
        self.csp_subarray_leaf_node = DeviceProxy("mid-tmc/subarray-leaf-node-csp/01")
        self.sdp_master_leaf_node = DeviceProxy("mid-tmc/leaf-node-sdp/0")

        proxies = [
            self.central_node,
            self.subarray_node,
            self.sdp_master_leaf_node,
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
        dp = DeviceProxy(f"mid-tmc/leaf-node-dish/{dish_id}")
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

    def __init__(self, cbf_sim_mode: bool = True):
        """.

        :param cbf_sim_mode: CBF simulation mode, defaults to True
        :type cbf_sim_mode: bool
        """
        self.controller = DeviceProxy("mid_csp_cbf/sub_elt/controller")
        self.subarray = DeviceProxy("mid_csp_cbf/sub_elt/subarray_01")
        self.fspcorrsubarray = DeviceProxy("mid_csp_cbf/fspcorrsubarray/01_01")
        if not cbf_sim_mode:
            self.bite = DeviceProxy("mid_csp_cbf/ec/bite")
            self.ec_deployer = DeviceProxy("mid_csp_cbf/ec/deployer")
        self.cbf_sim_mode = cbf_sim_mode

    def get_talon_board_proxy(self, board_num) -> DeviceProxy:
        """.

        :param board_num: _description_
        :type board_num: _type_
        :return: _description_
        :rtype: DeviceProxy
        """
        dp = DeviceProxy(f"mid_csp_cbf/talon_board/{board_num:03}")
        assert dp.ping() > 0
        return dp


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
            self.cbf_sim_mode = simulation_mode
        else:
            self.control.cbfSimulationMode = 0
            sleep(5)  # TODO: Enable use of events to check simulationmode
            # wait_for_event(self.control, "cbfSimulationMode", 1)
            self.cbf_sim_mode = simulation_mode


class Dish:
    """Helper class containing Dish specific details."""

    def __init__(self, sut_namespace: str, dish_id: str, sut_cluster_domain: str):
        """.

        :param sut_cluster_domain: Cluster domain of the central cluster
        :param sut_namespace: Namespace into which the SUT has been deployed
        :type sut_namespace: str
        :param dish_id: Dish ID with the SKA prefix e.g. SKA001
        :type dish_id: str
        """
        self.sut_namespace = sut_namespace
        self.sut_cluster_domain = sut_cluster_domain
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
        if self.sut_cluster_domain == "mid.internal.skao.int":
            return f"dish-lmc-{str.lower(self.dish_id)}"

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
        if self.sut_cluster_domain == "mid.internal.skao.int":
            return (
                f"tango-databaseds.{dish_namespace}.svc"
                f"{self.dish_id}.{self.sut_cluster_domain}:10000"
            )

        return f"tango-databaseds.{dish_namespace}.svc.{self.sut_cluster_domain}:10000"

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
        f"tango-databaseds.{settings['SUT_namespace']}.svc.{settings['sut_cluster_domain']}:10000"
    )
    os.environ["TANGO_HOST"] = TANGO_HOST
    os.environ["TZ"] = "Africa/Johannesburg"

    yield

    if CURRENT_TANGO_HOST:
        os.environ["TANGO_HOST"] = CURRENT_TANGO_HOST

    if CURRENT_TZ:
        os.environ["TZ"] = CURRENT_TZ


@pytest.fixture(scope="session")
def pb_and_eb_ids(settings) -> Tuple[str, str]:
    """Fixture for generating pb and eb ids for the scan.

    :param settings: test settings
    :type settings: dict
    :return: pb_id and eb_id for use in the assign_resources.json
    :rtype: Tuple[str, str]
    """
    time_now = localtime()
    date = strftime("%Y%m%d", time_now)
    time_now = strftime("%H%M%S", time_now)
    eb_id_prefix = settings["eb_id_prefix"]
    pb_id_prefix = settings["pb_id_prefix"]
    eb_id = f"{eb_id_prefix}-{date}-{time_now}"
    pb_id = f"{pb_id_prefix}-{date}-{time_now}"
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
    cbf = CBF(settings["sim_mode"])
    csp = CSP()
    dishes = [
        Dish(settings["SUT_namespace"], receptor, settings["sut_cluster_domain"])
        for receptor in RECEPTORS
    ]

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


@given("a sequence diagrammer has optionally started listening for events")
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

    sim_mode = settings["sim_mode"]

    # Load DishVCCConfig
    CONFIG_DATA_DIR = settings["data_dir"]
    CBF_CONFIGS = os.path.join(CONFIG_DATA_DIR, "cbf")
    DISH_CONFIG_FILE = f"{CBF_CONFIGS}/sys_params/load_dish_config.json"

    with open(DISH_CONFIG_FILE, encoding="utf-8") as f:
        dish_config_json = json.load(f)

    dish_config_json["tm_data_sources"][0] = "car:ska-mid?27.3.0#tmdata"
    dish_config_json["tm_data_filepath"] = (
        "instrument/ska1_mid_itf/vcc-config/ska-mid-cbf-system-parameters.json"
    )
    logger.debug(f"dish_config_json file contents: \n{dish_config_json}")

    is_k_value_correct = True
    raw_vcc_config = tmc.csp_master_leaf_node.dishVccConfig

    if tmc_central_node.isDishVccConfigSet and raw_vcc_config:
        try:
            dish_vcc_config = json.loads(tmc.csp_master_leaf_node.dishVccConfig)
            for receptor in RECEPTORS:
                if (
                    dish_vcc_config["dish_parameters"][receptor]["k"]
                    != settings["expected_k_value"]
                ):
                    is_k_value_correct = False
                    break
        except json.JSONDecodeError:
            logger.warning("dishVccConfig could not be decoded. Will re-load config.")

    if not raw_vcc_config or not tmc_central_node.isDishVccConfigSet or not is_k_value_correct:
        tmc_central_node.LoadDishCfg(json.dumps(dish_config_json))
        wait_for_event(tmc_central_node, "isDishVccConfigSet", True)

        logger.debug(json.dumps(dish_config_json))

        dish_config_artifact_path = f"{settings['artifact_dir']}/load_dish_config.json"
        with open(dish_config_artifact_path, "w") as dish_config_file:
            json.dump(dish_config_json, dish_config_file, indent=2)

        sleep(5)

    dish_vcc_config = json.loads(tmc.csp_master_leaf_node.dishVccConfig)

    for receptor in RECEPTORS:
        assert dish_vcc_config["dish_parameters"][receptor]["k"] == settings["expected_k_value"]

    # Turn ON the telescope
    assert cbf_fspcorrsubarray.obsstate == ObsState.IDLE
    assert tmc_subarray_node.obsState == ObsState.EMPTY
    assert csp_subarray_leaf_node.cspSubarrayObsState == ObsState.EMPTY
    assert sdp_subarray_leaf_node.sdpSubarrayObsState == ObsState.EMPTY

    if tmc_central_node.telescopeState == DevState.ON and cbf.controller.state == DevState.ON:
        logger.info("Telescope is already in the ON state. Not issuing TelescopeOn command.")
    else:
        # Turn ON the telescope
        logger.info("Issuing ON command")
        tmc_central_node.TelescopeOn()
        wait_for_event(tmc_central_node, "telescopeState", DevState.ON)

    # CBF On state indication is a combination of controller state and talon board health state
    wait_for_event(cbf.controller, "state", DevState.ON)

    # TEMP COMMIT: Seems like CBF requires all 4 talons to be healthy
    number_of_talons = 4

    if not sim_mode:
        for i in range(1, number_of_talons + 1):
            talon_board_dp = cbf.get_talon_board_proxy(i)
            wait_for_event(talon_board_dp, "healthState", HealthState.OK)

    assert tmc_central_node.telescopeState in [DevState.ON, DevState.UNKNOWN]
    for receptor in RECEPTORS:
        assert tmc.get_dish_leaf_node_dp(receptor).dishMode in [
            DishMode.STANDBY_FP,
            DishMode.OPERATE,
        ]


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
        assign_resources_json["sdp"]["processing_blocks"][0]["parameters"]["pod_settings"][0][
            "nodeSelector"
        ] = {"kubernetes.io/hostname": "za-itf-cloud03"}

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

        band_2_vis_channels = {
            "channels_id": "vis_band2_channels",
            "spectral_windows": [
              {
                "spectral_window_id": "fsp_1_channels",
                "count": 55380,
                "start": 0,
                "stride": 1,
                "freq_min": 940000000.0,
                "freq_max": 1684307200.0,
                "link_map": [
                  [
                    0,
                    0
                  ],
                  [
                    200,
                    1
                  ],
                  [
                    744,
                    2
                  ],
                  [
                    944,
                    3
                  ]
                ]
              }
            ]
          }

        assign_resources_json["sdp"]["execution_block"]["channels"].append(band_2_vis_channels)

        band_2_scan_type = {
            "scan_type_id": "science_band2",
            "derive_from": ".default",
            "beams": {
              "vis0": {
                "field_id": "field_a",
                "channels_id": "vis_band2_channels"
              }
            }
          }
          
        assign_resources_json["sdp"]["execution_block"]["scan_types"].append(band_2_scan_type)
        # del assign_resources_json["sdp"]["execution_block"]["scan_types"][0]["beams"]["vis0"]["channels_id"]
        # assign_resources_json["sdp"]["execution_block"]["scan_types"][1]["beams"]["channels_id"] = "vis_channels"

    logger.info(f"PB ID: {pb_id}, EB ID: {eb_id}")

    logger.debug(json.dumps(assign_resources_json))

    assign_resources_artifact_path = f"{settings['artifact_dir']}/assign_resources.json"
    with open(assign_resources_artifact_path, "w") as assign_resources_config_file:
        json.dump(assign_resources_json, assign_resources_config_file, indent=4)

    tmc.central_node.AssignResources(json.dumps(assign_resources_json))
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

    configure_scan_artifact_path = f"{settings['artifact_dir']}/configure_scan.json"
    with open(configure_scan_artifact_path, "w") as configure_scan_config_file:
        json.dump(configure_scan_json, configure_scan_config_file, indent=4)

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

    logger.debug(json.dumps(scan_json))

    scan_artifact_path = f"{settings['artifact_dir']}/scan.json"
    with open(scan_artifact_path, "w") as scan_config_file:
        json.dump(scan_json, scan_config_file, indent=2)

    tmc.subarray_node.Scan(scan_json)
    wait_for_event(tmc.sdp_subarray_leaf_node, "sdpSubarrayObsState", ObsState.SCANNING)
    wait_for_event(tmc.csp_subarray_leaf_node, "cspSubarrayObsState", ObsState.SCANNING)
    wait_for_event(tmc.subarray_node, "obsState", ObsState.SCANNING)
    logger.info(f"Scanning for {scan_time} seconds")
    sleep(scan_time)


@when(
    parsers.cfparse(
        "I execute {number_of_scans:Int} {scan_time:Number} second scans with"
        " a {delay_between_scans:Number} second delay between scans without"
        " reconfiguring or releasing resources",
        extra_types={"Number": float, "Int": int},
    )
)
def _(telescope_handlers, number_of_scans, scan_time, delay_between_scans, settings):
    """Execute multiple scans without releasing resources or reconfiguring.

    :param telescope_handlers: _description_
    :type settings: _type_
    :type telescope_handlers: _type_
    :param number_of_scans: Number of times the end-scan -> scan cycle is executed
    :type number_of_scans: float
    :param delay_between_scans: Duration of the delay between scans in seconds
    :type delay_between_scans: float
    :param scan_time: Duration of each scan in seconds
    :type scan_time: float
    """
    if settings["override_scan_duration"]:
        scan_time = int(settings["override_scan_duration"])

    if settings["override_multiscan_delay_between_scans"]:
        delay_between_scans = int(settings["override_multiscan_delay_between_scans"])

    if settings["override_multiscan_number_of_scans"]:
        number_of_scans = int(settings["override_multiscan_number_of_scans"])

    logger.info(
        f"Executing {number_of_scans} scans of {scan_time} seconds each with a"
        f" {delay_between_scans} second delay between scans"
    )

    tmc, _, _, _ = telescope_handlers

    SCAN_FILE = f"{settings['TMC_configs']}/scan.json"
    with open(SCAN_FILE, encoding="utf-8") as f:
        scan_json = json.load(f)

    for scan_number in range(1, number_of_scans + 1):
        # Execute scan
        scan_json["scan_id"] = scan_number
        scan_json["transaction_id"] = f"txn-....-{scan_number:05}"
        logger.debug(json.dumps(scan_json))
        scan_artifact_path = f"{settings['artifact_dir']}/scan.json"
        with open(scan_artifact_path, "w") as scan_config_file:
            json.dump(scan_json, scan_config_file, indent=2)

        logger.info(f"Starting scan {scan_number}/{number_of_scans}")
        tmc.subarray_node.Scan(json.dumps(scan_json))
        wait_for_event(tmc.sdp_subarray_leaf_node, "sdpSubarrayObsState", ObsState.SCANNING)
        wait_for_event(tmc.csp_subarray_leaf_node, "cspSubarrayObsState", ObsState.SCANNING)
        wait_for_event(tmc.subarray_node, "obsState", ObsState.SCANNING)
        logger.info(f"Scanning for {scan_time} seconds")

        # Hold scan for specified duration
        sleep(scan_time)

        # End scan
        logger.info(f"Ending scan {scan_number}/{number_of_scans}")
        tmc.subarray_node.EndScan()
        wait_for_event(tmc.sdp_subarray_leaf_node, "sdpSubarrayObsState", ObsState.READY)
        wait_for_event(tmc.csp_subarray_leaf_node, "cspSubarrayObsState", ObsState.READY)
        wait_for_event(tmc.subarray_node, "obsState", ObsState.READY)
        logger.info(f"Completed scan {scan_number}/{number_of_scans}")

        # Hold before next scan if not last scan
        if scan_number < number_of_scans:
            logger.info(f"Holding for {delay_between_scans} seconds before next scan")
            sleep(delay_between_scans)

@when(
    parsers.cfparse(
        "I execute {number_of_scans:Int} {scan_time:Number} second scans with"
        " a {delay_between_scans:Number} second delay between scans interchanging"
        " between band 1 and band 2 without releasing resources",
        extra_types={"Number": float, "Int": int},
    )
)
def _(telescope_handlers, number_of_scans, scan_time, delay_between_scans, receptor_ids, settings):
    """Execute multiple scans interchanging between band 1 and band 2 without releasing resources."""

    if settings["override_scan_duration"]:
        scan_time = int(settings["override_scan_duration"])

    if settings["override_multiscan_delay_between_scans"]:
        delay_between_scans = int(settings["override_multiscan_delay_between_scans"])

    if settings["override_multiscan_number_of_scans"]:
        number_of_scans = int(settings["override_multiscan_number_of_scans"])

    cycle_band = [1, 2]
    band_cycler = cycle(cycle_band)

    logger.info(
        f"Executing {number_of_scans} scans of {scan_time} seconds each with a"
        f" {delay_between_scans} second delay between scans interchanging between"
        f" the following bands: {list(set(cycle_band))}"
    )
    logger.info(f"{scan_time} {delay_between_scans} {number_of_scans}")
    tmc, _, _, _ = telescope_handlers

    # Setting up configure scan payload
    tmc, _, _, _ = telescope_handlers
    RECEPTORS = receptor_ids

    CONFIGURE_SCAN_FILE = f"{settings['TMC_configs']}/configure_scan.json"

    # Setting up scan payload
    SCAN_FILE = f"{settings['TMC_configs']}/scan.json"
    with open(SCAN_FILE, encoding="utf-8") as f:
        scan_json = json.load(f)

    for scan_number in range(1, number_of_scans + 1):
        # Configure scan
        scan_band = next(band_cycler)
        logger.info(f"Configuring scan {scan_number}/{number_of_scans}. Band {scan_band}")
        
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

            if scan_band == 2:
                configure_scan_json["sdp"]["scan_type"] = f"science_band2"
            elif scan_band == 1:
                configure_scan_json["sdp"]["scan_type"] = f"science"

            configure_scan_json["csp"]["transaction_id"] = f"txn-....-{scan_number:05}"
            # configure_scan_json["csp"]["common"]["config_id"] = f"4 receptor, band {scan_band}, 2 FSP, no options"
            configure_scan_json["tmc"]["scan_duration"] = float(scan_time)
            
            if scan_number > 1:
                configure_scan_json["tmc"]["partial_configuration"] = True

        logger.debug(json.dumps(configure_scan_json))

        configure_scan_artifact_path = f"{settings['artifact_dir']}/configure_scan.json"

        with open(configure_scan_artifact_path, "w") as configure_scan_config_file:
            json.dump(configure_scan_json, configure_scan_config_file, indent=4)

        tmc.subarray_node.Configure(json.dumps(configure_scan_json))
        wait_for_event(tmc.csp_subarray_leaf_node, "cspSubarrayObsState", ObsState.READY)
        wait_for_event(tmc.sdp_subarray_leaf_node, "sdpSubarrayObsState", ObsState.READY)
        for receptor in RECEPTORS:
            wait_for_event(tmc.get_dish_leaf_node_dp(receptor), "dishMode", DishMode.OPERATE)
        wait_for_event(tmc.subarray_node, "obsState", ObsState.READY)

        # Execute scan
        scan_json["scan_id"] = scan_number
        scan_json["transaction_id"] = f"txn-....-{scan_number:05}"
        logger.debug(json.dumps(scan_json))
        scan_artifact_path = f"{settings['artifact_dir']}/scan.json"
        with open(scan_artifact_path, "w") as scan_config_file:
            json.dump(scan_json, scan_config_file, indent=2)

        logger.info(f"Starting scan {scan_number}/{number_of_scans}")
        tmc.subarray_node.Scan(json.dumps(scan_json))
        wait_for_event(tmc.sdp_subarray_leaf_node, "sdpSubarrayObsState", ObsState.SCANNING)
        wait_for_event(tmc.csp_subarray_leaf_node, "cspSubarrayObsState", ObsState.SCANNING)
        wait_for_event(tmc.subarray_node, "obsState", ObsState.SCANNING)
        logger.info(f"Scanning for {scan_time} seconds")

        # Hold scan for specified duration
        sleep(scan_time)

        # End scan
        # logger.info(f"Ending scan {scan_number}/{number_of_scans}")
        # tmc.subarray_node.EndScan()
        wait_for_event(tmc.sdp_subarray_leaf_node, "sdpSubarrayObsState", ObsState.READY, timeout=(scan_time + 150))
        wait_for_event(tmc.csp_subarray_leaf_node, "cspSubarrayObsState", ObsState.READY)
        wait_for_event(tmc.subarray_node, "obsState", ObsState.READY)
        logger.info(f"Completed scan {scan_number}/{number_of_scans}")

        # Hold before next scan if not last scan
        if scan_number < number_of_scans:
            logger.info(f"Holding for {delay_between_scans} seconds before next scan")
            sleep(delay_between_scans)

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

    input_string_json = {
        "interface": "https://schema.skao.int/ska-tmc-releaseresources/2.0",
        "transaction_id": "txn-....-00001",
        "subarray_id": 1,
        "release_all": True,
        "receptor_ids": [],
    }
    input_string = json.dumps(input_string_json)
    tmc.central_node.ReleaseResources(input_string)

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


@given("HPS devices are configured")
def _(telescope_handlers):
    """Generate talon configuration files and download CBF artefacts if necessary.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    """
    logger.info("Configuring HPS devices")

    _, cbf, _, _ = telescope_handlers

    ec_deployer = cbf.ec_deployer

    # TODO: Tie this in with test config to avoid hardcoding here
    ec_deployer.targetTalons = [1, 2, 3, 4]
    ec_deployer.generate_config_jsons()
    ec_deployer.set_timeout_millis(900000)
    # TODO: Run only if the relevant artefacts are not already present.
    # TODO: Find a way to intelligently check if the correct artefacts are already present
    # ec_deployer.download_artifacts()
    ec_deployer.configure_db()
    ec_deployer.set_timeout_millis(3000)


@when("I generate BITE data")
def _(settings, telescope_handlers, bite_test_id):
    """Generate CBF BITE data using BITE configuraiton files.

    :param settings: _description_
    :type settings: _type_
    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    :param bite_test_id: _description_
    :type bite_test_id: _type_
    """
    _, cbf, _, _ = telescope_handlers

    cbf_controller = cbf.controller
    bite = cbf.bite

    CONFIG_DATA_DIR = settings["data_dir"]
    CBF_INPUT_DATA_DIR = os.path.join(CONFIG_DATA_DIR, "cbf/cbf_input_data")

    # File containing BITE config selectors and receptor sampling settings
    CBF_INPUT_FILE = os.path.join(CBF_INPUT_DATA_DIR, "cbf_input_data.json")

    # File containing BITE configs
    BITE_CONFIG_FILE = os.path.join(CBF_INPUT_DATA_DIR, "bite_config_parameters/bite_configs.json")

    # File containing BITE data filter configs
    FILTERS_FILE = os.path.join(CBF_INPUT_DATA_DIR, "bite_config_parameters/filters.json")

    files = [
        CBF_INPUT_FILE,
        BITE_CONFIG_FILE,
        FILTERS_FILE,
    ]

    for file in files:
        if not os.path.isfile(file):
            error = f"{file} does not exist"
            logger.error(error)
            pytest.fail(error)

    dishVccConfig = json.loads(cbf_controller.sysparam)
    logger.debug(f"dishVccConfig from CSP Master: \n{dishVccConfig}\n")

    with open(CBF_INPUT_FILE, encoding="utf-8") as f:
        cbf_input_config = json.load(f)["cbf_input_data"][bite_test_id]
        receptors = cbf_input_config["receptors"]

        # Use same k-value as in current dishVccConfig
        for receptor in receptors:
            dish_id = receptor["dish_id"]
            k_value = dishVccConfig["dish_parameters"][dish_id]["k"]
            receptor["sample_rate_k"] = k_value

    cbf_input_data_json = json.dumps(cbf_input_config)

    logger.info(f"CBF input data being used to generate BITE data: {cbf_input_data_json}")

    bite.load_cbf_input_data(cbf_input_data_json)

    with open(BITE_CONFIG_FILE, encoding="utf-8") as f:
        bite_config_data_json = json.dumps(json.load(f))

    bite.load_bite_config_data(bite_config_data_json)

    with open(FILTERS_FILE, encoding="utf-8") as f:
        filter_data_json = json.dumps(json.load(f))

    bite.load_filter_data(filter_data_json)

    # Wait for bite config and filter data to be loaded
    sleep(10)

    bite.set_timeout_millis(240000)
    logger.info("Generating data using CBF BITE")
    bite.generate_bite_data()
    bite.set_timeout_millis(6000)


@when("I start LSTV replay")
def _(telescope_handlers):
    """Start Long Sequence Test Vectors (LSTV) replay into CBF.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    """
    logger.info("Starting LSTV replay")
    _, cbf, _, _ = telescope_handlers

    bite = cbf.bite

    bite.start_lstv_replay()


@when("I stop LSTV replay")
def _(telescope_handlers):
    """Stop LSTV replay into CBF.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    """
    logger.info("Stopping LSTV replay")
    _, cbf, _, _ = telescope_handlers

    bite = cbf.bite

    bite.stop_lstv_replay()


@pytest.fixture
def bite_test_id(settings):
    """Generate test ID for BITE data generation.

    Reads the BITE_TEST_SELECTOR environment variable.
    Defaults to 'talon-001 basic gaussian noise' if unset.

    :param settings: _description_
    :type settings: Dict
    :return: _description_
    :rtype: String
    """
    # TODO: Move to settings
    BITE_TEST_SELECTOR = os.environ.get("BITE_TEST_SELECTOR", "talon-001 basic gaussian noise")

    CONFIG_DATA_DIR = settings["data_dir"]
    CBF_INPUT_DATA_DIR = os.path.join(CONFIG_DATA_DIR, "cbf/cbf_input_data")

    # File containing BITE config selectors and receptor sampling settings
    CBF_INPUT_FILE = os.path.join(CBF_INPUT_DATA_DIR, "cbf_input_data.json")

    with open(CBF_INPUT_FILE, encoding="utf-8") as f:
        cbf_input_configs = json.load(f)["cbf_input_data"]

    if BITE_TEST_SELECTOR not in cbf_input_configs:
        error = f"Invalid BITE test selector. '{BITE_TEST_SELECTOR}' not found in {CBF_INPUT_FILE}"
        logger.error(error)
        pytest.fail(error)

    return BITE_TEST_SELECTOR


@then("the telescope is in the released-resources state")
def _(telescope_handlers, receptor_ids):
    """Check that the telescope is in the released-resources state.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    :param receptor_ids: _description_
    :type receptor_ids: _type_
    """
    logger.info("Checking telescope state")
    _, cbf, _, _ = telescope_handlers
