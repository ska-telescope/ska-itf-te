"""features/test_configure_scan.feature feature tests."""

import logging
import os
from typing import Callable

import pytest
import tango
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.entry_points.base import EntryPoint
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from .. import conftest
from ..conftest import SutTestSettings
from ..resources.models.csp_model.entry_point import CSPEntryPoint

# pylint: disable=eval-used
logger = logging.getLogger(__name__)


# Set the number of subarray i.e. execution settings of the test.
CSPEntryPoint.nr_of_subarrays = 2
sut_settings = SutTestSettings
sut_settings.nr_of_subarrays = CSPEntryPoint.nr_of_subarrays


# pylint: disable=abstract-method
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import enum 


@pytest.fixture(name="nr_of_subarrays", autouse=True, scope="session")
def fxt_nr_of_subarrays() -> int:
    """_summary_.

    :return: _description_
    :rtype: int
    """
    # we only work with 1 subarray as CBF low currently limits
    # deployment of only 1
    # cbf mid only controls the state of subarray 1
    # so will also limit to 1
    tel = names.TEL()
    if tel.skalow:
        return 1
    return 2

@pytest.fixture(name="set_nr_of_subarray", autouse=True)
def fxt_set_nr_of_subarray(sut_settings: conftest.SutTestSettings, nr_of_subarrays: int):
    """
    Set the number of subarrays in the SUT settings.

    :param sut_settings: _description_
    :type sut_settings: conftest.SutTestSettings
    :param nr_of_subarrays: The number of subarrays to set in the SUT settings.
    :type nr_of_subarrays: int
    """
    sut_settings.nr_of_subarrays = nr_of_subarrays
    print(f"fxt_set_nr_of_subarray() nr_of_subarrays={nr_of_subarrays}")

@pytest.fixture(autouse=True, scope="session")
def fxt_set_csp_online_from_csp(
    set_session_exec_settings: fxt_types.session_exec_settings,
    set_subsystem_online: Callable[[EntryPoint], None],
    wait_sut_ready_for_session: Callable[[EntryPoint], None],
    nr_of_subarrays: int,
):
    """_summary_.

    :param nr_of_subarrays: _description_
    :type nr_of_subarrays: int
    :param set_subsystem_online: _description_
    :type set_subsystem_online: Callable[[EntryPoint], None]
    :param set_session_exec_settings: A fixture to set session execution settings.
    :type set_session_exec_settings: fxt_types.session_exec_settings
    :param wait_sut_ready_for_session: Fixture that is used to take a subsystem
                                       online using the given entrypoint.
    :type wait_sut_ready_for_session: Callable[[EntryPoint], None]
    """
    # we first wait in case csp is not ready
    set_session_exec_settings.time_out = 300
    set_session_exec_settings.log_enabled = True
    tel = names.TEL()
    set_session_exec_settings.capture_logs_from(str(tel.csp.subarray(1)))
    CSPEntryPoint.nr_of_subarrays = nr_of_subarrays
    entry_point = CSPEntryPoint()
    logging.info("wait for sut to be ready in the context of csp")
    wait_sut_ready_for_session(entry_point)
    logging.info("setting csp components online within csp context")
    entry_point = CSPEntryPoint()
    set_subsystem_online(entry_point)

@pytest.fixture(name="set_csp_entry_point", autouse=True)
def fxt_set_csp_entry_point(
    set_nr_of_subarray,
    set_session_exec_env: fxt_types.set_session_exec_env,
    exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """_summary_.

    :param set_nr_of_subarray: To set the number of subarray
    :type set_nr_of_subarray: int
    :param set_session_exec_env: _description_
    :type set_session_exec_env: fxt_types.set_session_exec_env
    :param exec_settings: _description_
    :type exec_settings: fxt_types.exec_settings
    :param sut_settings: _description_
    :type sut_settings: SutTestSettings
    """
    exec_env = set_session_exec_env
    if not sut_settings.mock_sut:
        CSPEntryPoint.nr_of_subarrays = sut_settings.nr_of_subarrays
        exec_env.entrypoint = CSPEntryPoint
    else:
        exec_env.entrypoint = "mock"
    exec_env.scope = ["csp"]
    sut_settings.default_subarray_name = sut_settings.tel.csp.subarray(sut_settings.subarray_id)
    print(f"fxt_set_csp_entry_point() sut_settings.default_subarray_name={sut_settings.default_subarray_name}")


@pytest.fixture(name="set_up_subarray_log_checking_for_csp")
@pytest.mark.usefixtures("set_csp_entry_point")
def fxt_set_up_log_checking_for_csp(
    log_checking: fxt_types.log_checking,
    sut_settings: SutTestSettings,
):
    """Set up log capturing (if enabled by CATPURE_LOGS).

    :param log_checking: The skallop log_checking fixture to use
    :param sut_settings: A class representing the settings for the system under test.
    """
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        csp_subarray = str(tel.csp.subarray(sut_settings.subarray_id))
        cbf_subarray = str(tel.csp.cbf.subarray(sut_settings.subarray_id))
        log_checking.capture_logs_from_devices(csp_subarray, cbf_subarray)


# transition monitoring
@pytest.fixture(autouse=True)
def fxt_setup_transition_monitoring(
    context_monitoring: fxt_types.context_monitoring,
):
    """
    Set up the transition monitoring.

    :param context_monitoring: An instance of the ContextMonitoring class
        containing context monitoring settings.
    :type context_monitoring: fxt_types.context_monitoring
    """
    tel = names.TEL()
    (
        context_monitoring.set_waiting_on(tel.csp.cbf.subarray(1))
        .for_attribute("obsstate")
        .and_observe()
    )


@pytest.fixture(name="csp_base_composition")
def fxt_csp_base_composition(tmp_path) -> conf_types.Composition:
    """Set up a base composition configuration to use for csp/cbf.

    :param tmp_path: a temporary path for sending configuration as a file.
    :return: the configuration settings.
    """
    composition = conf_types.CompositionByFile(tmp_path, conf_types.CompositionType.STANDARD)
    return composition


@pytest.fixture(name="csp_base_configuration")
def fxt_csp_base_configuration(tmp_path) -> conf_types.ScanConfiguration:
    """Set up a base scan configuration to use for csp/cbf.

    :param tmp_path: a temporary path for sending configuration as a file.
    :return: the configuration settings.
    """
    configuration = conf_types.ScanConfigurationByFile(
        tmp_path, conf_types.ScanConfigurationType.STANDARD
    )
    return configuration

@pytest.fixture(name="monitor_cbf")
def fxt_monitor_cbf(context_monitoring: fxt_types.context_monitoring):
    """
    Monitor the CBF.

    :param context_monitoring: An instance of the ContextMonitoring class
        containing context monitoring settings.
    :type context_monitoring: fxt_types.context_monitoring
    """
    tel = names.TEL()
    (
        context_monitoring.set_waiting_on(tel.csp.cbf.subarray(1))
        .for_attribute("obsstate")
        .and_observe()
    )
    #Set telescope on
    tel.on()


@scenario("features/test_configure_scan.feature", "Test ConfigureScan")
def test_test_configurescan():
    """Test ConfigureScan."""


@given("Telescope is on and its subsystems are in STANDBY_LP mode")
def telescope_is_on_standby_lp():
    tango_device_proxy = tango.DeviceProxy(f"mid-sdp/control/0")
    assert tango_device_proxy.state() == tango.DevState.STANDBY


@when("TMC commands the telescope to STANDBY_OPERATE mode")
def tmc_commands_telescope_to_operate():
    """TMC commands the telescope to STANDBY_OPERATE mode."""
    global csp_master
    csp_master = tango_device_proxy = tango.DeviceProxy(f"mid-sdp/control/0")
    csp_master.write_attribute("state", "STANDBY_OPERATE")


@then("Telescope subsystems must be in STANDBY_OPERATE mode")
def dish_structure_in_standby_mode():
    """Telescope subsystems must be in STANDBY_OPERATE mode."""
    tel = names.TEL()
    tmc = con_config.get_device_proxy(tel.skamid.controller)
    result = tmc.read_attribute("state").value
    assert_that(str(result)).is_equal_to("OPERATE")
