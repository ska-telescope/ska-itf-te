"""features/test_configure_scan.feature feature tests."""

import logging
import pytest
import os
from pytest_bdd import given, scenario, then, when
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.infra_mon.configuration import get_mvp_release
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_ser_skallop.mvp_control.describing.mvp_names import DeviceName
from ..resources.models.mvp_model.env import init_observation_config
from ..resources.models.csp_model.entry_point import CSPEntryPoint
from typing import Any, Callable, Concatenate, ParamSpec, TypeVar, cast
from assertpy import assert_that
from types import SimpleNamespace

from ..conftest import SutTestSettings
from .. import conftest

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


@pytest.mark.xfail(reason="Not implemented")
@when("I command it to LoadDishCfg")
def i_command_it_to_loaddishcfg():
    """I command it to LoadDishCfg."""
    csp_base_configuration: conf_types.ScanConfiguration
    return csp_base_configuration
    # raise NotImplementedError

# pylint: disable=eval-used


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
def fxt_set_nr_of_subarray(
    sut_settings: conftest.SutTestSettings,
    exec_settings: fxt_types.exec_settings,
    nr_of_subarrays: int,
):
    """_summary_.

    :param nr_of_subarrays: _description_
    :type nr_of_subarrays: int
    :param sut_settings: _description_
    :type sut_settings: conftest.SutTestSettings
    :param exec_settings: A fixture that returns the execution settings of the test
    :type exec_settings: fxt_types.exec_settings
    """
    CSPEntryPoint.nr_of_subarrays = nr_of_subarrays
    sut_settings.nr_of_subarrays = nr_of_subarrays

#Assign Resources
def i_assign_resources_to_it(
    running_telescope: fxt_types.running_telescope,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    sb_config: fxt_types.sb_config,
    composition: conf_types.Composition,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
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


@pytest.mark.xfail(reason="Not implemented")
@then("DS Operating mode attribute must be in STANDBY_OPERATE")
def ds_operating_mode_attribute_must_be_in_standby_operate():
    """DS Operating mode attribute must be in STANDBY_OPERATE."""
    tel = names.TEL()
    csp_master = con_config.get_device_proxy(tel.csp.controller)
    result = csp_master.read_attribute("state").value
    assert_that(str(result)).is_equal_to("OPERATE")
    sut_settings: conftest.SutTestSettings
    nr_of_subarrays = sut_settings.nr_of_subarrays
    for index in range(1, nr_of_subarrays + 1):
        subarray = con_config.get_device_proxy(tel.csp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(str(result)).is_equal_to("OPERATE")
