"""Sky Simulator components can be controlled remotely using Tango device server that communicates with Raspberry Pi using SCPI commands feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


@scenario('features/sky_simulator_controller.feature', 'Test SCPI device returns identity')
def test_test_scpi_device_returns_identity():
    """Test SCPI device returns identity."""


@scenario('features/sky_simulator_controller.feature', 'Test SkySimCtl can switch ON signal sources')
def test_test_skysimctl_can_switch_on_signal_sources():
    """Test SkySimCtl can switch ON signal sources."""


@given('the SkySimController is initialised (all signal sources OFF)')
def _():
    """the SkySimController is initialised (all signal sources OFF)."""
    raise NotImplementedError


@given('the SkySimController is online')
def _():
    """the SkySimController is online."""
    raise NotImplementedError


@when('I ask its identity')
def _():
    """I ask its identity."""
    raise NotImplementedError


@when('I switch on the <signal_source_name>')
def _():
    """I switch on the <signal_source_name>."""
    raise NotImplementedError


@then('it responds "SkySimController"')
def _():
    """it responds "SkySimController"."""
    raise NotImplementedError


@then('the <signal_source_name> must be ON')
def _():
    """the <signal_source_name> must be ON."""
    raise NotImplementedError

