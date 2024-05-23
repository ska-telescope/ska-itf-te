"""features/test_configure_scan.feature feature tests."""

import pytest
from pytest_bdd import given, scenario, then, when


@scenario("features/test_configure_scan.feature", "Test ConfigureScan")
def test_test_configurescan():
    """Test ConfigureScan."""


@pytest.mark.xfail(reason="Not implemented")
@given("DS Operating mode DSOperatingMode STANDBY_LP")
def ds_operating_mode_dsoperatingmode_standby_lp():
    """DS Operating mode DSOperatingMode STANDBY_LP."""
    # raise NotImplementedError


@pytest.mark.xfail(reason="Not implemented")
@when("I command it to LoadDishCfg")
def i_command_it_to_loaddishcfg():
    """I command it to LoadDishCfg."""
    # raise NotImplementedError


@pytest.mark.xfail(reason="Not implemented")
@then("DS Operating mode attribute must be in STANDBY_OPERATE")
def ds_operating_mode_attribute_must_be_in_standby_operate():
    """DS Operating mode attribute must be in STANDBY_OPERATE."""
    # raise NotImplementedError
