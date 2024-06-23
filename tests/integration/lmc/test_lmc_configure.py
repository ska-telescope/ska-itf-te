"""features/test_configure_scan.feature feature tests."""

import tango
from pytest_bdd import given, scenario, then, when

from ..dish_enums import DishMode


@scenario("features/test_configure_scan.feature", "Test ConfigureScan")
def test_configurescan():
    """Test ConfigureScan."""


@given("Telescope is on and its subsystems are in STANDBY_LP mode")
def telescope_is_on_standby_lp():
    """Test telescope is in standby low power mode."""
    tango_device_proxy = tango.DeviceProxy("ska001/elt/master")
    result = tango_device_proxy.read_attribute("dishMode").value
    assert DishMode(result) == DishMode.STANDBY_LP


@when("TMC commands the telescope to STANDBY_OPERATE mode")
def tmc_commands_telescope_to_operate():
    """TMC commands the telescope to STANDBY_OPERATE mode."""
    tango_device_proxy = tango.DeviceProxy("ska001/elt/master")
    tango_device_proxy.SetOperateMode()


@then("Telescope subsystems must be in STANDBY_OPERATE mode")
def dish_structure_in_standby_mode():
    """Telescope subsystems must be in STANDBY_OPERATE mode."""
    tango_device_proxy = tango.DeviceProxy("ska001/elt/master")
    result = tango_device_proxy.read_attribute("dishMode").value
    assert DishMode(result) == DishMode.OPERATE
