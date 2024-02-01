"""pytest global settings, fixtures and global bdd step implementations for integration tests."""
import logging
import os
from types import SimpleNamespace
from typing import Any, Callable, Concatenate, ParamSpec, TypeVar, cast

import pytest
from assertpy import assert_that
from mock import Mock
from pytest_bdd import given, parsers, then, when
from pytest_bdd.parser import Feature, Scenario, Step
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.describing.mvp_names import DeviceName
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.infra_mon.configuration import get_mvp_release
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from tango import DeviceProxy

from .resources.models.base.states import ObsState
from .resources.models.mvp_model.env import init_observation_config
from .resources.models.obsconfig.base import DishName
from .resources.models.obsconfig.config import Observation

logger = logging.getLogger(__name__)


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


def pytest_bdd_before_step_call(
    request: Any,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable[[Any], Any],
    step_func_args: dict[str, Any],
):
    """_summary_.

    :param request: _description_
    :type request: Any
    :param feature: _description_
    :type feature: Feature
    :param scenario: _description_
    :type scenario: Scenario
    :param step: _description_
    :type step: Step
    :param step_func: _description_
    :type step_func: Callable[[Any], Any]
    :param step_func_args: _description_
    :type step_func_args: dict[str, Any]
    """
    if os.getenv("SHOW_STEP_FUNCTIONS"):
        logger.info(
            "\n**********************************************************\n"
            f"***** {step.keyword} {step.name} *****\n"
            "**********************************************************"
        )


class SutTestSettings(SimpleNamespace):
    """Object representing env like SUT settings for fixtures in conftest."""

    mock_sut: bool = False
    nr_of_subarrays = 3
    subarray_id = 1
    scan_duration = 4
    _receptors = [1, 2, 3, 4]
    _nr_of_receptors = 4
    # specify if a specific test case needs running
    # for SDP visibility receive test: test_case = "vis-receive"
    test_case = None

    def __init__(self, **kwargs: Any) -> None:
        """_summary_.

        :param kwargs: _summary_.

        """
        super().__init__(**kwargs)
        self.tel = names.TEL()
        logger.info("initialising sut settings")
        self.observation = init_observation_config()
        self.default_subarray_name: DeviceName = self.tel.tm.subarray(self.subarray_id)
        self.disable_subarray_teardown = False
        self.restart_after_abort = False

    @property
    def nr_of_receptors(self):
        """_summary_.

        :return: _description_
        :rtype: _type_
        """
        return self._nr_of_receptors

    @nr_of_receptors.setter
    def nr_of_receptors(self, value: int):
        """_summary_.

        :param value: _description_
        :type value: int
        """
        self._nr_of_receptors = value
        self._receptors = [  # pylint: disable=unnecessary-comprehension
            i for i in range(1, value + 1)
        ]

    @property
    def receptors(self):
        """_summary_.

        :return: _description_
        :rtype: _type_
        """
        return self._receptors

    @receptors.setter
    def receptors(self, receptor: list[int]):
        """_summary_.

        :param receptor: _description_
        :type receptor: list[int]
        """
        self._receptors = receptor


@pytest.fixture(name="disable_clear")
def fxt_disable_abort(configured_subarray: fxt_types.configured_subarray):
    """_summary_.

    :param configured_subarray: _description_
    :type configured_subarray: fxt_types.configured_subarray
    """
    configured_subarray.disable_automatic_clear()


@pytest.fixture(name="sut_settings", scope="function", autouse=True)
def fxt_conftest_settings() -> SutTestSettings:
    """Fixture to use for setting env like  SUT settings for fixtures in conftest.

    :return: sut test settings
    """
    return SutTestSettings()


class _OnlineFlag:
    value: bool = False

    def __bool__(self):
        return self.value

    def set_true(self):
        """_summary_."""
        self.value = True


# setting systems online
@pytest.fixture(name="online", autouse=True, scope="session")
def fxt_online():
    """Set all systems online.

    :return: Flag representing the online status of all systems.
    :rtype: _type_
    """
    return _OnlineFlag()


@pytest.fixture(name="set_session_exec_settings", autouse=True, scope="session")
def fxt_set_session_exec_settings(
    session_exec_settings: fxt_types.session_exec_settings,
):
    """_summary_.

    :param session_exec_settings: _description_
    :type session_exec_settings: fxt_types.session_exec_settings
    :return: _description_
    :rtype: _type_
    """
    if os.getenv("ATTR_SYNCH_ENABLED_GLOBALLY"):
        # logger.warning("disabled attribute synchronization globally")
        session_exec_settings.attr_synching = True
    if os.getenv("LIVE_LOGGING_EXTENDED"):
        session_exec_settings.run_with_live_logging()
    return session_exec_settings


@pytest.fixture(name="set_exec_settings_from_env", autouse=True)
def fxt_set_exec_settings_from_env(exec_settings: fxt_types.exec_settings):
    """Set up general execution settings during setup and teardown.

    :param exec_settings: The global test execution settings as a fixture.
    """
    if os.getenv("LIVE_LOGGING_EXTENDED"):
        logger.info("running live logs globally")
        exec_settings.run_with_live_logging()
    if os.getenv("ATTR_SYNCH_ENABLED_GLOBALLY"):
        logger.warning("enabled attribute synchronization globally")
        exec_settings.attr_synching = True
    exec_settings.time_out = 150


@pytest.fixture(name="integration_test_exec_settings")
def fxt_integration_test_exec_settings(
    exec_settings: fxt_types.exec_settings,
) -> fxt_types.exec_settings:
    """Set up test specific execution settings.

    :param exec_settings: The global test execution settings as a fixture.
    :return: test specific execution settings as a fixture
    """
    integration_test_exec_settings = exec_settings.replica()
    integration_test_exec_settings.time_out = 150

    if os.getenv("LIVE_LOGGING"):
        integration_test_exec_settings.run_with_live_logging()
        logger.info("running live logs globally")
    if os.getenv("REPLAY_EVENTS_AFTERWARDS"):
        logger.info("replay log messages after waiting")
        integration_test_exec_settings.replay_events_afterwards()
    if os.getenv("ATTR_SYNCH_ENABLED"):
        logger.warning("enabled attribute synchronization")
        exec_settings.attr_synching = True
    if os.getenv("ATTR_SYNCH_ENABLED_GLOBALLY"):
        exec_settings.attr_synching = True
    return integration_test_exec_settings


@pytest.fixture(name="observation_config")
def fxt_observation_config(sut_settings: SutTestSettings) -> Observation:
    """Pytest fixture that provides an instance of the `Observation` class.

    This represents the observation configuration for the system under test.

    :param sut_settings: A class representing the settings for the system under test.
    :return: A class representing the observation configuration for the system under test.
    """
    return sut_settings.observation


@pytest.fixture(name="mocked_observation_config")
def fxt_mocked_observation_config(observation_config: Observation) -> Mock:
    """_summary_.

    :param observation_config: _description_
    :type observation_config: Observation
    :return: _description_
    :rtype: Mock
    """
    return Mock(spec=Observation, wraps=observation_config)


T = TypeVar("T")
P = ParamSpec("P")
R = TypeVar("R")


def _inject_method(injectable: T, method: Callable[Concatenate[T, P], R]) -> Callable[P, R]:
    def _replaced_method(*args: P.args, **kwargs: P.kwargs) -> R:
        return method(injectable, *args, **kwargs)

    return _replaced_method


ObservationConfigInterjector = Callable[[str, Callable[Concatenate[Observation, P], R]], None]


@pytest.fixture(name="interject_into_observation_config")
def fxt_observation_config_interjector(
    observation_config: Observation, mocked_observation_config: Mock
) -> ObservationConfigInterjector[P, R]:
    """_summary_.

    :param observation_config: _description_
    :type observation_config: Observation
    :param mocked_observation_config: _description_
    :type mocked_observation_config: Mock
    :return: _description_
    :rtype: ObservationConfigInterjector[P, R]
    """
    obs = observation_config

    def interject_observation_method(
        method_name: str, intj_fn: Callable[Concatenate[Observation, P], Any]
    ):
        injected_method = _inject_method(obs, intj_fn)
        mocked_observation_config.configure_mock(**{f"{method_name}.side_effect": injected_method})

    return interject_observation_method


# global when steps
# start up


@when("I start up the telescope")
def i_start_up_the_telescope(
    standby_telescope: fxt_types.standby_telescope,
    entry_point: fxt_types.entry_point,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    I start up the telescope.

    :param standby_telescope: The standby telescope instance to be started.
    :param entry_point: The entry point to the system under test.
    :param context_monitoring: The context monitoring configuration.
    :param integration_test_exec_settings: The integration test execution settings.
    """
    with context_monitoring.context_monitoring():
        with standby_telescope.wait_for_starting_up(integration_test_exec_settings):
            logger.info("The entry point being used is : %s", entry_point)
            entry_point.set_telescope_to_running()


@given("the Telescope is in ON state")
def the_telescope_is_on(
    standby_telescope: fxt_types.standby_telescope,
    entry_point: fxt_types.entry_point,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    I start up the telescope.

    :param standby_telescope: The standby telescope instance to be started.
    :param entry_point: The entry point to the system under test.
    :param context_monitoring: The context monitoring configuration.
    :param integration_test_exec_settings: The integration test execution settings.
    """
    standby_telescope.disable_automatic_setdown()
    with context_monitoring.context_monitoring():
        with standby_telescope.wait_for_starting_up(integration_test_exec_settings):
            logger.info("The entry point being used is : %s", entry_point)
            entry_point.set_telescope_to_running()


@when("I switch off the telescope")
def i_switch_off_the_telescope(
    running_telescope: fxt_types.running_telescope,
    entry_point: fxt_types.entry_point,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    I switch off the telescope.

    :param running_telescope: The running telescope instance.
    :param entry_point: The entry point to the system under test.
    :param context_monitoring: The context monitoring configuration.
    :param integration_test_exec_settings: The integration test execution settings.

    """
    # we disable automatic shutdown as this is done by the test itself
    running_telescope.disable_automatic_setdown()
    with context_monitoring.context_monitoring():
        with running_telescope.wait_for_shutting_down(integration_test_exec_settings):
            entry_point.set_telescope_to_standby()


@when(
    parsers.cfparse(
        "I assign dishes: {dish_ids:DishName+} to the subarray", extra_types={"DishName": str}
    )
)
def i_assign_dishes_to_it(
    running_telescope: fxt_types.running_telescope,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    sb_config: fxt_types.sb_config,
    composition: conf_types.Composition,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
    observation_config: Observation,
    dish_ids: list[str],
):
    """I assign resources to it.

    :param running_telescope: Dictionary containing the running telescope's devices
    :param context_monitoring: Object containing information about
        the context in which the test is being executed
    :param entry_point: Information about the entry point used for the test
    :param sb_config: Object containing the Subarray Configuration
    :param composition: Object containing information about the composition of the subarray
    :param integration_test_exec_settings: Object containing
        the execution settings for the integration test
    :param sut_settings: Object containing the system under test settings
    :param observation_config: the singleton Observation object used by the entrypoints
    :param dish_ids: the list of dish ids to assign to the subarray
    """
    observation_config.update_target_specs(dishes=cast(list[DishName], dish_ids))
    subarray_id = sut_settings.subarray_id
    receptors = sut_settings.receptors
    with context_monitoring.context_monitoring():
        with running_telescope.wait_for_allocating_a_subarray(
            subarray_id, receptors, integration_test_exec_settings
        ):
            entry_point.compose_subarray(
                subarray_id, receptors, composition, sb_config.sbid  # type: ignore
            )


@when("I assign resources to the subarray")
@when("I assign resources to it")
def i_assign_resources_to_it(
    running_telescope: fxt_types.running_telescope,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    sb_config: fxt_types.sb_config,
    composition: conf_types.Composition,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """I assign resources to it.

    :param running_telescope: Dictionary containing the running telescope's devices
    :param context_monitoring: Object containing information about
        the context in which the test is being executed
    :param entry_point: Information about the entry point used for the test
    :param sb_config: Object containing the Subarray Configuration
    :param composition: Object containing information about the composition of the subarray
    :param integration_test_exec_settings: Object containing
        the execution settings for the integration test
    :param sut_settings: Object containing the system under test settings
    """
    subarray_id = sut_settings.subarray_id
    receptors = sut_settings.receptors
    with context_monitoring.context_monitoring():
        with running_telescope.wait_for_allocating_a_subarray(
            subarray_id, receptors, integration_test_exec_settings
        ):
            entry_point.compose_subarray(
                subarray_id, receptors, composition, sb_config.sbid  # type: ignore
            )


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


@when("I command it to scan for a given period")
def i_execute_scan(
    configured_subarray: fxt_types.configured_subarray,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    I configure it for a scan.

    :param configured_subarray: The configured subarray.
    :param integration_test_exec_settings: The integration test execution settings.
    """
    configured_subarray.set_to_scanning(integration_test_exec_settings)


# scans
@given("an subarray busy scanning")
def i_command_it_to_scan(
    configured_subarray: fxt_types.configured_subarray,
    integration_test_exec_settings: fxt_types.exec_settings,
    context_monitoring: fxt_types.context_monitoring,
):
    """
    I configure it for a scan.

    :param configured_subarray: The configured subarray.
    :param integration_test_exec_settings: The integration test execution settings.
    :param context_monitoring: Context monitoring object.
    """
    integration_test_exec_settings.attr_synching = False
    with context_monitoring.context_monitoring():
        configured_subarray.set_to_scanning(integration_test_exec_settings)


@when("I release all resources assigned to it")
def i_release_all_resources_assigned_to_it(
    allocated_subarray: fxt_types.allocated_subarray,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    I release all resources assigned to it.

    :param allocated_subarray: The allocated subarray to be configured.
    :param context_monitoring: Context monitoring object.
    :param entry_point: The entry point to be used for the configuration.
    :param integration_test_exec_settings: The integration test execution settings.
    """
    sub_array_id = allocated_subarray.id

    with context_monitoring.context_monitoring():
        with allocated_subarray.wait_for_releasing_a_subarray(integration_test_exec_settings):
            entry_point.tear_down_subarray(sub_array_id)


@given("an subarray busy configuring")
def an_subarray_busy_configuring(
    allocated_subarray: fxt_types.allocated_subarray,
):
    """
    Given an subarray busy configuring.

    :param allocated_subarray: The allocated subarray to be configured.
    """
    allocated_subarray.set_to_configuring(clear_afterwards=False)
    allocated_subarray.disable_automatic_clear()


@given("an subarray busy assigning", target_fixture="allocated_subarray")
def an_subarray_busy_assigning(
    running_telescope: fxt_types.running_telescope,
    sb_config: fxt_types.sb_config,
    composition: conf_types.Composition,
    exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """Given an subarray busy assigning.

    Create a subarray but block only until it is in RESOURCING
    :param running_telescope: An object for running telescope
    :param sb_config: The SB configuration to use as context defaults to SBConfig()
    :param composition: The type of composition configuration to use
    :type composition: conf_types.Composition, optional
    :param exec_settings: A fixture that returns the execution settings of the test
    :param sut_settings: The settings of the system under test
    :return: A subarray context manager to ue for subsequent commands
    """
    subarray_id = sut_settings.subarray_id
    receptors = sut_settings.receptors
    allocated_subbaray = running_telescope.set_to_resourcing(
        subarray_id, receptors, sb_config, exec_settings, composition
    )
    allocated_subbaray.disable_automatic_teardown()
    return allocated_subbaray


@when("I command it to Abort")
def i_command_it_to_abort(
    context_monitoring: fxt_types.context_monitoring,
    allocated_subarray: fxt_types.allocated_subarray,
    entry_point: fxt_types.entry_point,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """_summary_.

    :param context_monitoring: _description_
    :type context_monitoring: fxt_types.context_monitoring
    :param allocated_subarray: _description_
    :type allocated_subarray: fxt_types.allocated_subarray
    :param entry_point: _description_
    :type entry_point: fxt_types.entry_point
    :param integration_test_exec_settings: _description_
    :type integration_test_exec_settings: fxt_types.exec_settings
    :param sut_settings: _description_
    :type sut_settings: SutTestSettings
    """
    subarray = sut_settings.default_subarray_name
    sub_array_id = sut_settings.subarray_id
    context_monitoring.builder.set_waiting_on(subarray).for_attribute(
        "obsstate"
    ).to_become_equal_to("ABORTED", ignore_first=False)
    with context_monitoring.context_monitoring():
        with context_monitoring.wait_before_complete(integration_test_exec_settings):
            if sut_settings.restart_after_abort:
                allocated_subarray.restart_after_test(integration_test_exec_settings)
            else:
                allocated_subarray.reset_after_test(integration_test_exec_settings)
            entry_point.abort_subarray(sub_array_id)

    integration_test_exec_settings.touch()


@then("the subarray should go into an aborted state")
def the_subarray_should_go_into_an_aborted_state(
    sut_settings: SutTestSettings,
):
    """_summary_.

    :param sut_settings: _description_
    :type sut_settings: SutTestSettings
    """
    subarray = con_config.get_device_proxy(sut_settings.default_subarray_name)
    result = subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.ABORTED)


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


class ResponseData(object):
    """Class to have response data received."""

    def __init__(self) -> None:
        """Initialise class variables."""
        self.response = None
        self.alarm_handler_device = DeviceProxy("alarm/handler/01")

    def clear_alarms(self):
        """Clear the configured alarms."""
        if self.response["alarm_summary"]["tag"] is not None:
            for tag in self.response["alarm_summary"]["tag"]:
                self.alarm_handler_device.Remove(tag)
            assert self.alarm_handler_device.alarmList == ()


@pytest.fixture(name="response_data")
def fixture_default_response():
    """Set up default responce.

    :yield: A class object representing default response for the system under test.
    """
    response_data = ResponseData()
    yield response_data
    response_data.clear_alarms()
