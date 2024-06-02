"""features/test_configure_scan.feature feature tests."""

import logging
import pytest
import json
import logging
import os
import pathlib
import time
from typing import List
from pytest_bdd import given, scenario, then, when
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.infra_mon.configuration import get_mvp_release
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_ser_skallop.mvp_control.describing.mvp_names import DeviceName
from typing import Any
from assertpy import assert_that
from ska_oso_pdm.entities.common.target import (
    CrossScanParameters,
    FivePointParameters,
    RasterParameters,
    SinglePointParameters,
    StarRasterParameters,
)
from ska_oso_pdm.entities.sdp import BeamMapping
from ska_oso_scripting import oda_helper
from ska_oso_scripting.functions.devicecontrol.resource_control import get_request_json
from ska_oso_scripting.objects import SubArray, Telescope
from ska_mid_jupyter_notebooks.cluster.cluster import Environment, TangoDeployment
from ska_mid_jupyter_notebooks.dish.dish import TangoDishDeployment
from ska_mid_jupyter_notebooks.helpers.path import project_root
from ska_mid_jupyter_notebooks.obsconfig.config import ObservationSB
from ska_mid_jupyter_notebooks.obsconfig.target_spec import TargetSpec, get_default_target_specs_sb
from ska_mid_jupyter_notebooks.sut.rendering import TelescopeMononitorPlot
from ska_mid_jupyter_notebooks.obsconfig.config import ObservationSB
from ska_mid_jupyter_notebooks.sut.state import TelescopeDeviceModel, get_telescope_state
from ska_tmc_cdm.messages.subarray_node.configure.core import ReceiverBand
from ska_tmc_cdm.messages.subarray_node.configure import ConfigureRequest
from ska_mid_jupyter_notebooks.sut.sut import TangoSUTDeployment, disable_qa
from ska_mid_jupyter_notebooks.test_equipment.rendering import get_test_equipment_monitor_plot
from ska_mid_jupyter_notebooks.test_equipment.state import get_equipment_model
from ska_mid_jupyter_notebooks.test_equipment.test_equipment import TangoTestEquipment
from ska_tmc_cdm.messages.central_node.sdp import Channel
from ska_tmc_cdm.messages.central_node.assign_resources import AssignResourcesRequest
import ska_ser_logging
from ..conftest import SutTestSettings
from .. import conftest


logger = logging.getLogger(__name__)
dish_ids = None
observation = None
target_specs = None
debug_mode = None
sub = None
scan_def_id = None
@pytest.fixture(name="check_infra_per_test", autouse=True)
def fxt_check_infra_per_test(check_infra_per_session: Any) -> Any:
    """Set a fixture to automatically check infra per test.

    :param check_infra_per_session: reference to session checking
    """
    if os.getenv("CHECK_INFRA_PER_TEST"):
        logger.info("checking infra health before executing test")
        if check_infra_per_session:
            release = check_infra_per_session
        else:
            release = get_mvp_release()
        if release.devices_health != "READY":
            devices = release.get_devices_not_ready()
            logger.exception(f"the following devices are not ready:\n: {devices}")


@scenario("features/test_configure_scan.feature", "Test ConfigureScan")
def test_test_configurescan():
    """Test ConfigureScan."""


@pytest.mark.skamid
@pytest.mark.lmc
@pytest.mark.assign
@given("DS Operating mode DSOperatingMode STANDBY_LP")
def ds_operating_mode_dsoperatingmode_standby_lp():
    """DS Operating mode DSOperatingMode STANDBY_LP."""
    # raise NotImplementedError
    #/*****************************************************************************************************/
    global debug_mode
    enable_logging = True  # This enables logging and sets the global log_level to debug
    dishlmc_enabled = True  # Set this to true if you have a dish LMC deployment
    global observation
    global dish_ids
    global target_specs
    global sub
    global scan_def_id
    debug_mode = True  # This setting enables printing of diagnostics
    executon_environment = Environment.CI
    branch_name = (
        "at-1952-comm"  # Set this if you are using an on-demand deployment (i.e. Environment.CI)
    )
    if enable_logging:
        ska_ser_logging.configure_logging(logging.DEBUG)
    test_equipment = TangoTestEquipment()
    print(f"Test Equipment Configured: {test_equipment}")
    # namespace_override parameter can be used to override auto-configured SUT namespace
    sut_namespace_override = ""
    subarray_count = 1
    subarray_id = 1
    sut = TangoSUTDeployment(
        branch_name,
        executon_environment,
        namespace_override=sut_namespace_override,
        subarray_index=subarray_id,
    )
    print(f"SUT configured: {str(sut)}")
    dish_ids = ["001"] #, "036"]
    # namespace_override parameter can be used to override auto-configured dish namespace
    dish_namespace_overrides = ["", ""]
    dish_deployments: List[TangoDishDeployment] = []
    if dishlmc_enabled:
        for i, d in enumerate(dish_ids):
            dish = TangoDishDeployment(
                f"ska{d}",
                branch_name=branch_name,
                environment=executon_environment,
                namespace_override=dish_namespace_overrides[i],
            )
            print(f"Dish {d} configured: {dish}")
            dish_deployments.append(dish)

    timestr = time.strftime("%Y%m%d-%H%M")
    notebook_output_dir = pathlib.Path(
        project_root(), f"notebook-execution-data/configure_scan_for_commissioning/execution-{timestr}"
    )
    os.makedirs(notebook_output_dir, exist_ok=True)
    # we disable qa as it is not been properly verified
    disable_qa()
    #/*****************************************************************************************************/
    #****************************
    test_equipment.turn_online()
    #*************Configure telescope monitoring*****************
    # setup monitoring
    # use telescope state object for state monitoring
    device_model = TelescopeDeviceModel(dish_ids, subarray_count)
    telescope_state = get_telescope_state(device_model, sut)
    # use monitor plot as a dashboard
    telescope_monitor_plot = TelescopeMononitorPlot(plot_width=900, plot_height=200)
    # set up events to monitor
    telescope_state.subscribe_to_on_off(telescope_monitor_plot.observe_telescope_on_off)
    telescope_state.subscribe_to_subarray_resource_state(
        telescope_monitor_plot.observe_subarray_resources_state
    )
    telescope_state.subscribe_to_subarray_configurational_state(
        telescope_monitor_plot.observe_subarray_configuration_state
    )
    telescope_state.subscribe_to_subarray_scanning_state(
        telescope_monitor_plot.observe_subarray_scanning_state
    )
    #/*****************************************************************************************************/
    #*****************************Print Dish-LMC Diagnostics***********************************************
    for dish_deployment in dish_deployments:
        print(f"Dish {dish_deployment.dish_id} - {dish_deployment.namespace}: Diagnostics")
    dish_deployment.print_diagnostics()
    #/*******************************************************************************************************/
    sub = SubArray(subarray_id)
    tel = Telescope()

    #Load VCC Configuration in TMC
    # This should only be executed for a fresh deployment (i.e. Telescope is OFF.
    # If you have restarted the subarray, you should not run this command
    sut.load_dish_vcc_config()

    # set Telescope to ON only if OFF
    # If you have restarted the subarray, you should not run this command (Telescope is already ON)
    # dish_lmc mode must be in LP_standby and before trying to turn the telescope ON
    # Takes about 1m20s
    if telescope_monitor_plot.on_off_state == "OFF":  # e.g. purple
        tel.on()
    else:
        assert (
            telescope_monitor_plot.on_off_state == "ON"
        ), f"Cant continue with telescope in {telescope_monitor_plot.on_off_state}"

#Observation definition***********************************************************************************
    dish_ids = [d.dish_id.upper() for d in dish_deployments]
    default_target_specs = get_default_target_specs_sb(dish_ids)
    observation = ObservationSB(target_specs=default_target_specs)
    target_specs = {
        "flux calibrator": TargetSpec(
            target_sb_detail={
                "co_ordinate_type": "Equatorial",
                "ra": "19:24:51.05 degrees",
                "dec": "-29:14:30.12 degrees",
                "reference_frame": "ICRS",
                "unit": ("hourangle", "deg"),
                "pointing_pattern_type": {
                    "single_pointing_parameters": SinglePointParameters(
                        offset_x_arcsec=0.0, offset_y_arcsec=0.0
                    ),
                    "raster_parameters": RasterParameters(
                        row_length_arcsec=0.0,
                        row_offset_arcsec=0.0,
                        n_rows=1,
                        pa=0.0,
                        unidirectional=False,
                    ),
                    "star_raster_parameters": StarRasterParameters(
                        row_length_arcsec=0.0,
                        n_rows=1,
                        row_offset_angle=0.0,
                        unidirectional=False,
                    ),
                    "five_point_parameters": FivePointParameters(offset_arcsec=0.0),
                    "cross_scan_parameters": CrossScanParameters(offset_arcsec=0.0),
                    "active_pointing_pattern_type": "single_pointing_parameters",
                },
            },
            scan_type="flux calibrator",
            band=ReceiverBand.BAND_2,
            channelisation="vis_channels9",
            polarisation="all",
            processing="test-receive-addresses",
            dish_ids=dish_ids,
            target=None,
        ),
        "M87": TargetSpec(
            target_sb_detail={
                "co_ordinate_type": "Equatorial",
                "ra": "19:24:51.05 degrees",
                "dec": "-29:14:30.12 degrees",
                "reference_frame": "ICRS",
                "unit": ("hourangle", "deg"),
                "pointing_pattern_type": {
                    "single_pointing_parameters": SinglePointParameters(
                        offset_x_arcsec=0.0, offset_y_arcsec=0.0
                    ),
                    "raster_parameters": RasterParameters(
                        row_length_arcsec=0.0,
                        row_offset_arcsec=0.0,
                        n_rows=1,
                        pa=0.0,
                        unidirectional=False,
                    ),
                    "star_raster_parameters": StarRasterParameters(
                        row_length_arcsec=0.0,
                        n_rows=1,
                        row_offset_angle=0.0,
                        unidirectional=False,
                    ),
                    "five_point_parameters": FivePointParameters(offset_arcsec=0.0),
                    "cross_scan_parameters": CrossScanParameters(offset_arcsec=0.0),
                    "active_pointing_pattern_type": "single_pointing_parameters",
                },
            },
            scan_type="M87",
            band=ReceiverBand.BAND_2,
            channelisation="vis_channels10",
            polarisation="all",
            processing="test-receive-addresses",
            dish_ids=dish_ids,
            target=None,
        ),
    }


    channel_configuration = [
        Channel(
            spectral_window_id="fsp_1_channels",
            count=14880,
            start=0,
            stride=2,
            freq_min=0.35e9,
            freq_max=0.368e9,
            link_map=[[0, 0], [200, 1], [744, 2], [944, 3]],
        )
    ]

    for key, value in target_specs.items():
        observation.add_channel_configuration(value.channelisation, channel_configuration)

    observation.add_target_specs(target_specs)

    for target_id, target in target_specs.items():
        observation.add_scan_type_configuration(
            config_name=target_id,
            beams={"vis0": BeamMapping(beam_id="vis0", field_id="M83")},
            derive_from=".default",
        )
    scan_def_id = "flux calibrator"
    observation.add_scan_sequence([scan_def_id])
#*************Create scheduling block definition instance and save it to ODA***********************

os.environ["ODA_URI"] = (
    "http://ingress-nginx-controller-lb-default.ingress-nginx.svc.miditf.internal.skao.int/ska-db-oda/api/v1/"
)

eb_id = oda_helper.create_eb()
print(f"Execution Block ID: {eb_id}")
observation.eb_id = eb_id
pdm_allocation = observation.generate_pdm_object_for_sbd_save(target_specs)

sbd = oda_helper.save(pdm_allocation)
sbd_id = sbd.sbd_id
pdm_allocation.sbd_id = sbd_id
print(f"Saved Scheduling Block Definition Instance in ODA: SBD_ID={sbd_id}")
#**************************************************************************

#*******************Assign resources***************************************
assign_request = observation.generate_allocate_config_sb(pdm_allocation).as_object

if debug_mode:
    request_json = get_request_json(assign_request, AssignResourcesRequest, True)
    print("AssignResourcesRequest:", json.dumps(json.loads(request_json), indent=2))

sub.assign_from_cdm(assign_request, timeout=120)
#*****************************************************************************

#*****************************Configure Scan**********************************
configure_object = observation.generate_scan_config_sb(
    pdm_observation_request=pdm_allocation,
    scan_definition_id=scan_def_id,
    scan_duration=10.0,
).as_object

if debug_mode:
    cfg_json = get_request_json(configure_object, ConfigureRequest)
    print(f"ConfigureRequest={cfg_json}")

sub.configure_from_cdm(configure_object, timeout=120)
time.sleep(2)
#****************************************************************************

#****************************Tear down***************************************
sub.end()
#telescope_monitor_plot.show()
sub.release()
#telescope_monitor_plot.show()
#****************************************************************************
@pytest.mark.xfail(reason="Not implemented")
@when("I command it to LoadDishCfg")
def i_command_it_to_loaddishcfg():
    """I command it to LoadDishCfg."""
    csp_base_configuration: conf_types.ScanConfiguration
    return csp_base_configuration
    # raise NotImplementedError

# scan configuration
@when("I configure it for a scan")
def i_configure_it_for_a_scan(
    allocated_subarray: fxt_types.allocated_subarray,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    configuration: conf_types.ScanConfiguration,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """
    I configure it for a scan.

    :param allocated_subarray: The allocated subarray to be configured.
    :param context_monitoring: Context monitoring object.
    :param entry_point: The entry point to be used for the configuration.
    :param configuration: The scan configuration to be used for the scan.
    :param integration_test_exec_settings: The integration test execution settings.
    :param sut_settings: SUT settings object.
    """
    sub_array_id = allocated_subarray.id
    sb_id = allocated_subarray.sb_config.sbid
    scan_duration = sut_settings.scan_duration

    with context_monitoring.context_monitoring():
        with allocated_subarray.wait_for_configuring_a_subarray(integration_test_exec_settings):
            entry_point.configure_subarray(sub_array_id, configuration, sb_id, scan_duration)


@pytest.mark.xfail(reason="Not implemented")
@then("DS Operating mode attribute must be in STANDBY_OPERATE")
def ds_operating_mode_attribute_must_be_in_standby_operate():
    """DS Operating mode attribute must be in STANDBY_OPERATE."""
    tel = names.TEL()
    csp_master = con_config.get_device_proxy(tel.skamid.controller)
    result = csp_master.read_attribute("state").value
    assert_that(str(result)).is_equal_to("OPERATE")
    sut_settings: conftest.SutTestSettings
    nr_of_subarrays = sut_settings.nr_of_subarrays
    for index in range(1, nr_of_subarrays + 1):
        subarray = con_config.get_device_proxy(tel.csp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(str(result)).is_equal_to("OPERATE")
