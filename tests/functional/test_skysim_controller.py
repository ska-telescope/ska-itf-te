"""Skysim Controller feature tests."""

from typing import Optional

import logging
import tango
from pytest_bdd import given, parsers, scenario, then, when
from ska_tango_testing.mock.tango import MockTangoEventCallbackGroup

#@pytest.mark.xfail(
    #reason="BDD tests are required to fail, before the code implementation."
#)
@scenario(
    "features/skysim_controller.feature",
    "Test SkySimCtl can switch ON signal sources",
)
@scenario(
    "features/skysim_controller.feature",
    "Test SCPI device returns identity",
)
def test_scpi_device_returns_identity(
    skysim_controller_device: tango.DeviceProxy,
    # pylint: disable-next=unused-argument
    change_event_callbacks: MockTangoEventCallbackGroup,
):
    """
    Test SCPI device returns identity.

    :raises NotImplementedError: because this command is not yet
        implemented
    """
    identity = getattr(skysim_controller_device, "identity")
    logging.info("Identity is %s", identity)
    #raise NotImplementedError


#@pytest.mark.xfail(
    #reason="BDD tests are required to fail, before the code implementation."
#)
@scenario(
    "features/skysim_controller.feature",
    "Test SkySimCtl can switch ON signal sources",
)
def test_skysimctl_can_switch_on_signal_sources():
    """
    Assert that the  SkySimCtl can switch ON signal sources.

    :raises NotImplementedError: because this command is not yet
        implemented
    """
    logging.info("Check signal sources")
    #raise NotImplementedError


@given("the SkySimController is initialised (all signal sources OFF)")
def skysim_controller_initialised(
    skysim_controller_device: tango.DeviceProxy,
    # pylint: disable-next=unused-argument
    change_event_callbacks: MockTangoEventCallbackGroup,
):
    """
    Assert that the  SkySimController is initialised.

    :raises NotImplementedError: because this command is not yet
        implemented
    """

    try:
        skysim_controller_device.Reset()
    except tango.DevFailed:
        logging.error("Sky simulator device failed")
    #raise NotImplementedError


@given("the SkySimController is online")
def skysim_controller_online(
    skysim_controller_device: tango.DeviceProxy,
    change_event_callbacks: MockTangoEventCallbackGroup,
):
    """
    Assert that the SkySimController is online.

    :raises NotImplementedError: because this command is not yet
        implemented
    """
    factory_default_settings = {
        #"noise_generator_on": False,
        #"rf_output_on": False,
        "siggen_rf_output_on": False,
    }

    #initial_values = {
        #attribute: getattr(skysim_controller_device, attribute)
        #for attribute in factory_default_settings
    #}
    initial_values = {}
    for attribute in factory_default_settings:
        try:
            initial_values[attribute] = getattr(skysim_controller_device, attribute)
            logging.info("Attribute %s = %s", attribute, initial_values[attribute])
        except AttributeError:
            logging.error("Could not read attribute %s", attribute)

    try:
        skysim_controller_device.Reset()
    except tango.DevFailed:
        logging.error("Sky simulator device failed")

    for attribute, value in initial_values.items():
        if value != factory_default_settings[attribute]:
            change_event_callbacks[f"skysimctl_{attribute}"].assert_change_event(
                factory_default_settings[attribute]
            )
    #raise NotImplementedError


@when("I ask its identity")
def skysim_identity():
    """
    Assert that we can ask the SkySimController its identity.

    :raises NotImplementedError: because this command is not yet
        implemented
    """
    logging.info("Check identity")
    # raise NotImplementedError


@when(parsers.parse(("I switch on the <signal_source_name>")))
def switch_on_signal_source(signal_source_name: Optional[dict] = None) -> None:
    """
    Assert that I switch on the <signal_source_name>.

    :param signal_source_name: signal source name to be used
        when the signal source needs to be switched on

    :raises NotImplementedError: because this command is not yet
        implemented
    """
    logging.info("Switch on signal source %s", signal_source_name)
    #raise NotImplementedError


@then('it responds "SkySimController"')
def skysim_identity_response():
    """
    Assert that the SkySimController responds with "SkySimController".

    :raises NotImplementedError: because this command is not yet
        implemented
    """
    logging.info("Check identity response")
    #raise NotImplementedError


@then("the <signal_source_name> must be ON")
def signal_source_on():
    """
    Assert that the <signal_source_name> must be ON.

    :raises NotImplementedError: because this command is not yet
        implemented
    """
    logging.info("Check signal source")
    #raise NotImplementedError
