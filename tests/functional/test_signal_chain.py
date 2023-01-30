"""This module contains BBD tests for a test equipment signal chain."""
from __future__ import annotations

import gc
import time

import pytest
import tango
from pytest_bdd import given, parsers, scenario, then, when
from ska_control_model import AdminMode
from ska_tango_testing.mock.tango import MockTangoEventCallbackGroup

# TODO: Oh no! Our hang-at-garbage-collection bug is back.
# I'm now blaming pytest-bdd. We need to do some diagnosis and report a bug.
gc.disable()


@pytest.mark.skip()
@scenario(
    "features/signal_chain.feature",
    "Test connection between Signal Generator and Spectrum Analyser",
)
def test_connection_between_siggen_and_spectana() -> None:
    """
    Test the connection between signal generator and spectrum analyser.

    Any code in this scenario method is run at the *end* of the
    scenario.
    """


@given("the Signal Generator is online")
def put_signal_generator_online(
    signal_generator_device: tango.DeviceProxy,
    change_event_callbacks: MockTangoEventCallbackGroup,
) -> None:
    """
    Connect to signal generator.

    We do two things in this step:

    1. Subscribe to change events on signal generator attributes that we
       care about

    2. Get the signal generator device online and on.

    :param signal_generator_device: the signal generator Tango device
        under test.
    :param change_event_callbacks: dictionary of mock change event
        callbacks with asynchrony support
    """
    starting_admin_mode = signal_generator_device.adminMode
    signal_generator_device.subscribe_event(
        "adminMode",
        tango.EventType.CHANGE_EVENT,
        change_event_callbacks["siggen_adminMode"],
    )
    change_event_callbacks.assert_change_event("siggen_adminMode", starting_admin_mode)

    starting_state = signal_generator_device.state()
    signal_generator_device.subscribe_event(
        "state",
        tango.EventType.CHANGE_EVENT,
        change_event_callbacks["siggen_state"],
    )
    change_event_callbacks.assert_change_event("siggen_state", starting_state)

    for attribute_name in ["frequency", "power_dbm", "rf_output_on"]:
        signal_generator_device.subscribe_event(
            attribute_name,
            tango.EventType.CHANGE_EVENT,
            change_event_callbacks[f"siggen_{attribute_name}"],
        )
    for attribute_name in ["frequency", "power_dbm", "rf_output_on"]:
        change_event_callbacks[f"siggen_{attribute_name}"].assert_against_call()

    if starting_admin_mode != AdminMode.ONLINE:
        signal_generator_device.adminMode = AdminMode.ONLINE
        change_event_callbacks.assert_change_event("siggen_adminMode", AdminMode.ONLINE)
        assert signal_generator_device.adminMode == AdminMode.ONLINE

        if starting_state == tango.DevState.DISABLE:
            change_event_callbacks.assert_change_event(
                "siggen_state", tango.DevState.UNKNOWN
            )
            change_event_callbacks.assert_change_event(
                "siggen_state", tango.DevState.ON
            )
            assert signal_generator_device.state() == tango.DevState.ON

            for attribute_name in ["frequency", "power_dbm", "rf_output_on"]:
                try:
                    change_event_callbacks[
                        f"siggen_{attribute_name}"
                    ].assert_against_call(
                        attribute_quality=tango.AttrQuality.ATTR_VALID
                    )
                except AssertionError:
                    # If the device had previously polled the instrument and
                    # obtained valid values, before it was taken offline, and
                    # these values have not changed since, then we will not
                    # receive change events when the device is put back online.
                    # Here, we want to consume any change events (so that they
                    # don't arrive unexpectedly in a future test step), without
                    # failing if not change event arrived.
                    # TODO: This should be fixed upstream in ska-tango-testing
                    # e.g. a `callback.consume_change_event()`` method.
                    pass


@given("the Signal Generator is initialised")
def initialise_signal_generator(
    signal_generator_device: tango.DeviceProxy,
    change_event_callbacks: MockTangoEventCallbackGroup,
) -> None:
    """
    Reset the signal generator.

    This test first reads attributes of the signal generator, and takes
    note of any values that are different from the factory defaults. It
    then resets the signal generator, and expects to receive change
    events for any attributes whose values needed to be restored to
    factory default.

    :param signal_generator_device: the signal generator Tango device
        under test.
    :param change_event_callbacks: dictionary of mock change event
        callbacks with asynchrony support
    """
    factory_default_settings = {
        "frequency": pytest.approx(10000000.0),
        "power_dbm": pytest.approx(0.0),
        "rf_output_on": False,
    }

    initial_values = {
        attribute: getattr(signal_generator_device, attribute)
        for attribute in factory_default_settings
    }

    signal_generator_device.Reset()

    for attribute, value in initial_values.items():
        if value != factory_default_settings[attribute]:
            change_event_callbacks[f"siggen_{attribute}"].assert_change_event(
                factory_default_settings[attribute]
            )


@given("the Signal Generator RF output is OFF")
def turn_off_signal_generator_rf_output(
    signal_generator_device: tango.DeviceProxy,
    change_event_callbacks: MockTangoEventCallbackGroup,
) -> None:
    """
    Check that RF output is off, and turn it off if necessary.

    :param signal_generator_device: the signal generator Tango device
        under test.
    :param change_event_callbacks: dictionary of mock change event
        callbacks with asynchrony support
    """
    if signal_generator_device.rf_output_on:
        signal_generator_device.rf_output_on = False
        change_event_callbacks["siggen_rf_output_on"].assert_change_event(False)
        assert not signal_generator_device.rf_output_on


@given("the Spectrum Analyser is online")
def put_spectrum_analyser_online(
    spectrum_analyser_device: tango.DeviceProxy,
    change_event_callbacks: MockTangoEventCallbackGroup,
) -> None:
    """
    Connect to spectrum analyser.

    We do two things in this step:

    1. Subscribe to change events on spectrum analyser attributes that we
       care about;

    2. Get the spectrum analyser device online and on.

    :param spectrum_analyser_device: the spectrum analyser Tango device
        under test.
    :param change_event_callbacks: dictionary of mock change event
        callbacks with asynchrony support
    """
    starting_admin_mode = spectrum_analyser_device.adminMode
    spectrum_analyser_device.subscribe_event(
        "adminMode",
        tango.EventType.CHANGE_EVENT,
        change_event_callbacks["spectana_adminMode"],
    )
    change_event_callbacks.assert_change_event(
        "spectana_adminMode", starting_admin_mode
    )

    starting_state = spectrum_analyser_device.state()
    spectrum_analyser_device.subscribe_event(
        "state",
        tango.EventType.CHANGE_EVENT,
        change_event_callbacks["spectana_state"],
    )
    change_event_callbacks.assert_change_event("spectana_state", starting_state)

    for attribute_name in [
        "frequency_start",
        "frequency_stop",
        "frequency_peak",
        "power_peak",
    ]:
        spectrum_analyser_device.subscribe_event(
            attribute_name,
            tango.EventType.CHANGE_EVENT,
            change_event_callbacks[f"spectana_{attribute_name}"],
        )
    for attribute_name in [
        "frequency_start",
        "frequency_stop",
        "frequency_peak",
        "power_peak",
    ]:
        change_event_callbacks[f"spectana_{attribute_name}"].assert_against_call()

    if starting_admin_mode != AdminMode.ONLINE:
        spectrum_analyser_device.adminMode = AdminMode.ONLINE
        change_event_callbacks.assert_change_event(
            "spectana_adminMode", AdminMode.ONLINE
        )
        assert spectrum_analyser_device.adminMode == AdminMode.ONLINE

        if starting_state == tango.DevState.DISABLE:
            change_event_callbacks.assert_change_event(
                "spectana_state", tango.DevState.UNKNOWN
            )
            change_event_callbacks.assert_change_event(
                "spectana_state", tango.DevState.ON
            )
            assert spectrum_analyser_device.state() == tango.DevState.ON

            for attribute_name in [
                "frequency_start",
                "frequency_stop",
                "frequency_peak",
                "power_peak",
            ]:
                try:
                    change_event_callbacks[
                        f"spectana_{attribute_name}"
                    ].assert_against_call(
                        attribute_quality=tango.AttrQuality.ATTR_VALID
                    )
                except AssertionError:
                    # If the device had previously polled the instrument and
                    # obtained valid values, before it was taken offline, and
                    # these values have not changed since, then we will not
                    # receive change events when the device is put back online.
                    # Here, we want to consume any change events (so that they
                    # don't arrive unexpectedly in a future test step), without
                    # failing if not change event arrived.
                    # TODO: This should be fixed upstream in ska-tango-testing
                    # e.g. a `callback.consume_change_event()`` method.
                    pass


@given("the Spectrum Analyser is initialised")
def initialise_spectrum_analyser(
    spectrum_analyser_device: tango.DeviceProxy,
    change_event_callbacks: MockTangoEventCallbackGroup,
) -> None:
    """
    Reset the spectrum analyser.

    This test first reads attributes of the spectrum analyser, and takes
    note of any values that are different from the factory defaults. It
    then resets the spectrum analyser, and expects to receive change
    events for any attributes whose values needed to be restored to
    factory default.

    :param spectrum_analyser_device: the signal generator Tango device
        under test.
    :param change_event_callbacks: dictionary of mock change event
        callbacks with asynchrony support
    """
    factory_default_settings = {
        "frequency_start": pytest.approx(1.4175e9),
        "frequency_stop": pytest.approx(1.5825e9),
    }

    initial_values = {
        attribute: getattr(spectrum_analyser_device, attribute)
        for attribute in factory_default_settings
    }

    spectrum_analyser_device.Reset()

    for attribute, value in initial_values.items():
        if value != factory_default_settings[attribute]:
            change_event_callbacks[f"spectana_{attribute}"].assert_change_event(
                factory_default_settings[attribute]
            )


@when(
    parsers.parse(
        "the user specifies the Spectrum Analyser stop frequency as "
        "{frequency_stop:f} Hz"
    )
)
def set_spectrum_analyser_frequency_stop(
    spectrum_analyser_device: tango.DeviceProxy,
    frequency_stop: float,
    change_event_callbacks: MockTangoEventCallbackGroup,
) -> None:
    """
    Set the stop frequency of the spectrum analyser.

    :param spectrum_analyser_device: the signal generator Tango device
        under test.
    :param frequency_stop: the top of the frequency range to be analysed
        by the spectrum analyser
    :param change_event_callbacks: dictionary of mock change event
        callbacks with asynchrony support
    """
    if spectrum_analyser_device.frequency_stop != pytest.approx(frequency_stop):
        spectrum_analyser_device.frequency_stop = frequency_stop
        change_event_callbacks["spectana_frequency_stop"].assert_change_event(
            pytest.approx(frequency_stop)
        )


@when(
    parsers.parse(
        "the user specifies the Spectrum Analyser start frequency as "
        "{frequency_start:f} Hz"
    )
)
def set_spectrum_analyser_frequency_start(
    spectrum_analyser_device: tango.DeviceProxy,
    frequency_start: float,
    change_event_callbacks: MockTangoEventCallbackGroup,
) -> None:
    """
    Set the start frequency of the spectrum analyser.

    :param spectrum_analyser_device: the signal generator Tango device
        under test.
    :param frequency_start: the bottom of the frequency range to be
        analysed by the spectrum analyser
    :param change_event_callbacks: dictionary of mock change event
        callbacks with asynchrony support
    """
    if spectrum_analyser_device.frequency_start != pytest.approx(frequency_start):
        spectrum_analyser_device.frequency_start = frequency_start
        change_event_callbacks["spectana_frequency_start"].assert_change_event(
            pytest.approx(frequency_start),
            lookahead=2,
        )
        # Lookahead=2 because if the stop is set below the current
        # start, the start will also be changed to just below the stop.


@when(
    parsers.parse(
        "the user specifies the Signal Generator frequency as {frequency:f} Hz"
    )
)
def set_signal_generator_frequency(
    signal_generator_device: tango.DeviceProxy,
    frequency: float,
    change_event_callbacks: MockTangoEventCallbackGroup,
) -> None:
    """
    Set the frequency of the signal generator RF output.

    :param signal_generator_device: the signal generator Tango device
        under test.
    :param frequency: the RF output frequency, in Hertz.
    :param change_event_callbacks: dictionary of mock change event
        callbacks with asynchrony support
    """
    if signal_generator_device.frequency != pytest.approx(frequency):
        signal_generator_device.frequency = frequency
        change_event_callbacks["siggen_frequency"].assert_change_event(
            pytest.approx(frequency)
        )


@when(parsers.parse("the user specifies the Signal Generator power as {power:f} dBm"))
def set_signal_generator_power(
    signal_generator_device: tango.DeviceProxy,
    power: float,
    change_event_callbacks: MockTangoEventCallbackGroup,
) -> None:
    """
    Set the power of the signal generator RF output.

    :param signal_generator_device: the signal generator Tango device
        under test.
    :param power: the power of the RF output, in dBm.
    :param change_event_callbacks: dictionary of mock change event
        callbacks with asynchrony support
    """
    if signal_generator_device.power_dbm != pytest.approx(power):
        signal_generator_device.power_dbm = power
        change_event_callbacks["siggen_power_dbm"].assert_change_event(
            pytest.approx(power)
        )


@when("the user turns the Signal Generator RF output ON")
def turn_signal_generator_rf_output_on(
    signal_generator_device: tango.DeviceProxy,
    change_event_callbacks: MockTangoEventCallbackGroup,
) -> None:
    """
    Turn on the signal generator's RF output.

    :param signal_generator_device: the signal generator Tango device
        under test.
    :param change_event_callbacks: dictionary of mock change event
        callbacks with asynchrony support
    """
    if not signal_generator_device.rf_output_on:
        signal_generator_device.rf_output_on = True
        change_event_callbacks["siggen_rf_output_on"].assert_change_event(True)


@then(
    parsers.parse(
        "the Spectrum Analyser peak frequency is approximately {frequency:f} " "Hz"
    )
)
def check_spectrum_analyser_frequency_peak_is(
    spectrum_analyser_device: tango.DeviceProxy,
    frequency: float,
    deployment_has_simulators: bool,
) -> None:
    """
    Check that the spectrum analyser frequency peak is as expected.

    :param spectrum_analyser_device: a proxy to the spectrum analyser
        Tango device.
    :param frequency: the expected frequency of the peak, in Hz
    :param deployment_has_simulators: whether this test is running in a
        deployment with simulators. If there are simulators present,
        this test will be skipped, since we cannot expect a spectrum
        analyser to really trace a signal from a signal generator, if
        one or both of them are simulated.
    """
    if deployment_has_simulators:
        pytest.skip("Test step must be run against hardware.")
        return
    # TODO: We can't use change_event_callbacks here. Since the frequency peak
    # may change slightly from poll to poll, we don't know how many change
    # events we have already received, before the change event we expect to
    # see. We could use change_event_callbacks if there were a way to clear out
    # previously received events; but ska-tango-testing does not currently
    # support this. The easily way to handle this is to fall back to the old
    # sleep-then-read-the-attribute approach.
    time.sleep(15)
    assert spectrum_analyser_device.frequency_peak == pytest.approx(frequency, rel=1e-3)


@then(parsers.parse("the Spectrum Analyser peak power is no more than {power:f} dBm"))
def check_spectrum_analyser_power_peak_is_no_more_than(
    spectrum_analyser_device: tango.DeviceProxy,
    power: float,
    deployment_has_simulators: bool,
) -> None:
    """
    Check that the spectrum analyser power peak is no more than expected.

    :param spectrum_analyser_device: a proxy to the spectrum analyser
        Tango device.
    :param power: the maximum expected power, in dBm
    :param deployment_has_simulators: whether this test is running in a
        deployment with simulators. If there are simulators present,
        this test will be skipped, since we cannot expect a spectrum
        analyser to really trace a signal from a signal generator, if
        one or both of them are simulated.
    """
    if deployment_has_simulators:
        pytest.skip("Test step must be run against hardware.")
        return
    # TODO: Characterise the expected attenuation so that we can make a
    # more meaningful assertion here.
    assert spectrum_analyser_device.power_peak <= power
