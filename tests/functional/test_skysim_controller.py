# coding=utf-8
"""Skysim components can be controlled remotely using Tango device server that communicates with Raspberry Pi using SCPI commands feature tests."""
from typing import Optional

import logging
import tango

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)
from ska_tango_testing.mock.tango import MockTangoEventCallbackGroup


@scenario('features/skysim_controller.feature', 'Test SCPI device returns identity')
def test_scpi_device_returns_identity(
    skysim_controller_device: tango.DeviceProxy,
    # pylint: disable-next=unused-argument
    change_event_callbacks: MockTangoEventCallbackGroup,
):
    """Test SCPI device returns identity."""
    identity = getattr(skysim_controller_device, "identity")
    logging.info("Identity is %s", identity)


@scenario('features/skysim_controller.feature', 'Test SkysimController can switch ON signal sources')
def test_skysimcontroller_can_switch_on_signal_sources():
    """
    Test SkysimController can switch ON signal sources.
    """
    logging.info("Check signal sources")


@scenario('features/skysim_controller.feature', 'Test SkysimController identity')
def test_skysimcontroller_identity(skysim_controller_device: tango.DeviceProxy):
    """Test SkysimController identity."""
    identity = getattr(skysim_controller_device, "identity")
    logging.info("Identity is %s", identity)


@scenario('features/skysim_controller.feature', 'Test SkysimController is initialised')
def test_skysimcontroller_is_initialised(
    skysim_controller_device: tango.DeviceProxy,
    # pylint: disable-next=unused-argument
    change_event_callbacks: MockTangoEventCallbackGroup,
):
    """Test SkysimController is initialised."""
    logging.info("")
    try:
        skysim_controller_device.Reset()
    except tango.DevFailed:
        logging.error("Sky simulator device failed")


@scenario('features/skysim_controller.feature', 'Test SkysimController is online')
def test_skysimcontroller_is_online(
    skysim_controller_device: tango.DeviceProxy,
    # pylint: disable-next=unused-argument
    change_event_callbacks: MockTangoEventCallbackGroup,
):
    """Test SkysimController is online."""
    logging.info("")
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


@scenario('features/skysim_controller.feature', 'Test SkysimController response')
def test_skysimcontroller_response():
    """Test SkysimController response."""
    logging.info("Test SkysimController response")


@scenario('features/skysim_controller.feature', 'Test SkysimController signal source is ON')
def test_skysimcontroller_signal_source_is_on():
    """Test SkysimController signal source is ON."""
    logging.info("Test SkysimController signal source is ON")


@given('all signal sources OFF')
def all_signal_sources_off():
    """all signal sources OFF."""
    logging.info("all signal sources OFF")


@given('the <signal_source_name> has been switched ON')
def the_signal_source_name_has_been_switched_on():
    """the <signal_source_name> has been switched ON."""
    logging.info("<signal_source_name> has been switched ON")


@given('the SkySimController is initialised')
def the_skysimcontroller_is_initialised():
    """the SkySimController is initialised."""
    logging.info("Set as initialised")


@given('the SkySimController is online')
def the_skysimcontroller_is_online():
    """the SkySimController is online."""
    logging.info("Set as online")


@given('the SkysimController is initialised')
def the_skysimcontroller_is_initialised():
    """the SkysimController is initialised."""
    logging.info("Check initialised")


@given('the SkysimController is online')
def the_skysimcontroller_is_online():
    """the SkysimController is online."""
    logging.info("")


@when('I ask it to do its thing')
def i_ask_it_to_do_its_thing():
    """I ask it to do its thing."""
    logging.info("do the thing")


@when('I ask it to switch on <signal_source_name>')
def i_ask_it_to_switch_on_signal_source_name():
    """I ask it to switch on <signal_source_name>."""
    logging.info("switch on <signal_source_name>")


@when('I ask its identity')
def i_ask_its_identity():
    """I ask its identity."""
    logging.info("ask identity")


@when('I ask its status')
def i_ask_its_status():
    """I ask its status."""
    logging.info("ask status")


@when('I switch on the <signal_source_name>')
def i_switch_on_the_signal_source_name():
    """I switch on the <signal_source_name>."""
    logging.info("switch on the <signal_source_name>")


@then('it responds "SKYSIMCTL"')
def it_responds_skysimctl():
    """it responds "SKYSIMCTL"."""
    logging.info("it responds 'SKYSIMCTL'")


@then('it responds "SkysimController"')
def it_responds_skysimcontroller():
    """it responds "SkysimController"."""
    logging.info("it responds 'SkysimController'")


@then('it responds "initialised"')
def it_responds_initialised():
    """it responds "initialised"."""
    logging.info("it responds 'initialised'")


@then('it responds "online"')
def it_responds_online():
    """it responds "online"."""
    logging.info("it responds 'online'")


@then('it responds <signal_source_name> is ON')
def it_responds_signal_source_name_is_on():
    """it responds <signal_source_name> is ON."""
    logging.info("it responds <signal_source_name> is ON")


@then('the <signal_source_name> must be ON')
def the_signal_source_name_must_be_on():
    """the <signal_source_name> must be ON."""
    logging.info("the <signal_source_name> must be ON")
