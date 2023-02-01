"""Sky Simulator Controller feature tests."""

from typing import Optional

import pytest
from pytest_bdd import given, parsers, scenario, then, when


@pytest.mark.xfail(
    reason="BDD tests are required to fail, before the code implementation."
)
@scenario(
    "features/sky_simulator_controller.feature",
    "Test SkySimCtl can switch ON signal sources",
)
@scenario(
    "features/sky_simulator_controller.feature",
    "Test SCPI device returns identity",
)
def test_scpi_device_returns_identity():
    """
    Test SCPI device returns identity.

    :raises NotImplementedError: because this command is not yet
        implemented
    """
    raise NotImplementedError


@pytest.mark.xfail(
    reason="BDD tests are required to fail, before the code implementation."
)
@scenario(
    "features/sky_simulator_controller.feature",
    "Test SkySimCtl can switch ON signal sources",
)
def test_skysimctl_can_switch_on_signal_sources():
    """
    Assert that the  SkySimCtl can switch ON signal sources.

    :raises NotImplementedError: because this command is not yet
        implemented
    """
    raise NotImplementedError


@given("the SkySimController is initialised (all signal sources OFF)")
def skysim_controller_initialised():
    """
    Assert that the  SkySimController is initialised.

    :raises NotImplementedError: because this command is not yet
        implemented
    """
    raise NotImplementedError


@given("the SkySimController is online")
def skysim_controller_online():
    """
    Assert that the SkySimController is online.

    :raises NotImplementedError: because this command is not yet
        implemented
    """
    raise NotImplementedError


@when("I ask its identity")
def skysim_identity():
    """
    Assert that we can ask the SkySimController its identity.

    :raises NotImplementedError: because this command is not yet
        implemented
    """
    raise NotImplementedError


@when(parsers.parse(("I switch on the <signal_source_name>")))
def switch_on_signal_source(signal_source_name: Optional[dict] = None) -> None:
    """
    Assert that I switch on the <signal_source_name>.

    :param signal_source_name: signal source name to be used
        when the signal source needs to be switched on

    :raises NotImplementedError: because this command is not yet
        implemented
    """
    raise NotImplementedError


@then('it responds "SkySimController"')
def skysim_identity_response():
    """
    Assert that the SkySimController responds with "SkySimController".

    :raises NotImplementedError: because this command is not yet
        implemented
    """
    raise NotImplementedError


@then("the <signal_source_name> must be ON")
def signal_source_on():
    """
    Assert that the <signal_source_name> must be ON.

    :raises NotImplementedError: because this command is not yet
        implemented
    """
    raise NotImplementedError
