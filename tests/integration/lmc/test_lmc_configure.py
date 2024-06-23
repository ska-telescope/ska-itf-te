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
from ..dish_enums import SPFOperatingMode
from ..resources.models.csp_model.entry_point import CSPEntryPoint
from ska_ser_skallop.event_handling.builders import get_message_board_builder

# Set the number of subarray i.e. execution settings of the test.
CSPEntryPoint.nr_of_subarrays = 2
sut_settings = SutTestSettings
sut_settings.nr_of_subarrays = CSPEntryPoint.nr_of_subarrays

import enum 
@scenario("features/test_configure_scan.feature", "Test ConfigureScan")
def test_configurescan():
    """Test ConfigureScan."""


@given("Telescope is on and its subsystems are in STANDBY_LP mode")
def telescope_is_on_standby_lp():
    tango_device_proxy = tango.DeviceProxy(f"mid-dish/simulator-spfc/ska001")
    result = tango_device_proxy.read_attribute("operatingMode").value
    assert SPFOperatingMode(result) == SPFOperatingMode.STANDBY_LP

@when("TMC commands the telescope to STANDBY_OPERATE mode")
def tmc_commands_telescope_to_operate():
    """TMC commands the telescope to STANDBY_OPERATE mode."""
    tango_device_proxy = tango.DeviceProxy(f"mid-dish/simulator-spfc/ska001")
    tango_device_proxy.operatingMode = SPFOperatingMode.OPERATE
    


@then("Telescope subsystems must be in STANDBY_OPERATE mode")
def dish_structure_in_standby_mode():
    """Telescope subsystems must be in STANDBY_OPERATE mode."""
    tango_device_proxy = tango.DeviceProxy(f"mid-dish/simulator-spfc/ska001")
    result = tango_device_proxy.read_attribute("operatingMode").value
    assert SPFOperatingMode(result) == SPFOperatingMode.OPERATE
