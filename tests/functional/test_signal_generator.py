"""This module contains BBD tests for Signal Generator scenarios."""
from __future__ import annotations

import queue

import pytest
import tango
from pytest_bdd import given, parsers, scenario, then, when
from ska_control_model import AdminMode
from ska_tango_testing.mock.tango import MockTangoEventCallbackGroup


@pytest.fixture(name="error_queue")
def error_queue_fixture() -> queue.SimpleQueue[tango.DevFailed]:
    """
    Return a queue for storing and retrieving any caught exceptions.

    :return: a queue of exceptions.
    """
    return queue.SimpleQueue()


@scenario(
    "features/signal_generator.feature",
    "Test a Signal Generator frequency and power can be set",
)
def test_sig_gen_set_freq_and_power() -> None:
    """Placeholder for real BDD test."""


@given("the Signal Generator is online")
def connect(
    signal_generator_device: tango.DeviceProxy,
    change_event_callbacks: MockTangoEventCallbackGroup,
) -> None:
    """
    Connect to signal generator.

    We do two things in this step:

    1. Subscribe to change events on attributes that we care about

    2. Get the device online and on.

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
    change_event_callbacks.assert_change_event(
        "siggen_adminMode", starting_admin_mode
    )

    starting_state = signal_generator_device.state()
    signal_generator_device.subscribe_event(
        "state",
        tango.EventType.CHANGE_EVENT,
        change_event_callbacks["siggen_state"],
    )
    change_event_callbacks.assert_change_event("siggen_state", starting_state)

    device_attribute_list = signal_generator_device.get_attribute_list()
    for attribute_name in [
        "identity",
        "frequency",
        "power_dbm",
        "rf_output_on",
        "query_error",
        "device_error",
        "execution_error",
        "command_error",
        "power_cycled",
    ]:
        assert attribute_name in device_attribute_list

        signal_generator_device.subscribe_event(
            attribute_name,
            tango.EventType.CHANGE_EVENT,
            change_event_callbacks[f"siggen_{attribute_name}"],
        )

    for attribute_name in [
        "identity",
        "frequency",
        "power_dbm",
        "rf_output_on",
        "query_error",
        "device_error",
        "execution_error",
        "command_error",
        "power_cycled",
    ]:
        change_event_callbacks[
            f"siggen_{attribute_name}"
        ].assert_against_call()

    if starting_admin_mode != AdminMode.ONLINE:
        signal_generator_device.adminMode = AdminMode.ONLINE
        change_event_callbacks.assert_change_event(
            "siggen_adminMode", AdminMode.ONLINE
        )
        assert signal_generator_device.adminMode == AdminMode.ONLINE

        if starting_state == tango.DevState.DISABLE:
            change_event_callbacks.assert_change_event(
                "siggen_state", tango.DevState.UNKNOWN
            )
            change_event_callbacks.assert_change_event(
                "siggen_state", tango.DevState.ON
            )
            assert signal_generator_device.state() == tango.DevState.ON

            for attribute_name in [
                "query_error",
                "frequency",
                "device_error",
                "power_dbm",
                "execution_error",
                "command_error",
                "rf_output_on",
                "power_cycled",
            ]:
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
def initialise(
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


@when(
    parsers.parse(
        "the user specifies the Signal Generator frequency as {frequency:d} Hz"
    )
)
def set_frequency(
    signal_generator_device: tango.DeviceProxy,
    frequency: float,
    error_queue: queue.SimpleQueue[tango.DevFailed],
) -> None:
    """
    Set frequency.

    :param signal_generator_device: the signal generator Tango device
        under test.
    :param frequency: the frequency setting, in MHz
    :param error_queue: a queue for storing errors
    """
    try:
        signal_generator_device.frequency = frequency
    except tango.DevFailed as dev_failed:
        error_queue.put(dev_failed)


@when(
    parsers.parse(
        "the user specifies the Signal Generator power as {power:d} dBm"
    )
)
def set_power(
    signal_generator_device: tango.DeviceProxy,
    power: float,
    error_queue: queue.SimpleQueue[tango.DevFailed],
) -> None:
    """
    Set power.

    :param signal_generator_device: the signal generator Tango device
        under test.
    :param power: the power setting, in dBm
    :param error_queue: a queue for storing errors
    """
    try:
        signal_generator_device.power_dbm = power
    except tango.DevFailed as dev_failed:
        error_queue.put(dev_failed)


@then(parsers.parse("the Signal Generator frequency is set as {frequency:d}"))
def check_frequency(
    signal_generator_device: tango.DeviceProxy,
    change_event_callbacks: MockTangoEventCallbackGroup,
    frequency: float,
) -> None:
    """
    Check that the specified frequency is set.

    :param signal_generator_device: the signal generator Tango device
        under test.
    :param change_event_callbacks: dictionary of mock change event
        callbacks with asynchrony support
    :param frequency: the frequency setting, in MHz
    """
    change_event_callbacks["siggen_frequency"].assert_change_event(
        pytest.approx(frequency)
    )
    assert signal_generator_device.frequency == pytest.approx(frequency)


@then(parsers.parse("the Signal Generator power is set as {power:d}"))
def check_power(
    signal_generator_device: tango.DeviceProxy,
    change_event_callbacks: MockTangoEventCallbackGroup,
    power: float,
) -> None:
    """
    Check that the specified power is set.

    :param signal_generator_device: the signal generator Tango device
        under test.
    :param change_event_callbacks: dictionary of mock change event
        callbacks with asynchrony support
    :param power: the power setting, in dBm
    """
    change_event_callbacks["siggen_power_dbm"].assert_change_event(
        pytest.approx(power)
    )
    assert signal_generator_device.power_dbm == pytest.approx(power)


@scenario(
    "features/signal_generator.feature",
    "Test a Signal Generator frequency can not be set with a negative value",
)
def test_sig_gen_set_invalid_frequency() -> None:
    """Placeholder for real BDD test."""


@then("the Signal Generator returns an error message")
def check_invalid_frequency_error(
    error_queue: queue.SimpleQueue[tango.DevFailed],
) -> None:
    """
    Check that the frequency write resulted in :py:exc:`tango.DevFailed` error.

    :param error_queue: a queue for storing errors
    """  # noqa: DAR401
    assert not error_queue.empty()
    with pytest.raises(
        tango.DevFailed,
        match="Set value for attribute frequency is below the minimum",
    ):
        raise error_queue.get_nowait()


@scenario(
    "features/signal_generator.feature",
    "Test a Signal Generator output can be turned ON",
)
def test_sig_gen_set_output_on() -> None:
    """Placeholder for real BDD test."""


@given("the Signal Generator RF Output is OFF")
def given_output_off(
    signal_generator_device: tango.DeviceProxy,
    change_event_callbacks: MockTangoEventCallbackGroup,
) -> None:
    """
    Check that RF output is off.

    :param signal_generator_device: the signal generator Tango device
        under test.
    :param change_event_callbacks: dictionary of mock change event
        callbacks with asynchrony support
    """
    if signal_generator_device.rf_output_on:
        signal_generator_device.rf_output_on = False
        change_event_callbacks["siggen_rf_output_on"].assert_change_event(
            False
        )
        assert not signal_generator_device.rf_output_on


@when("the user turns the Signal Generator RF Output ON")
def set_output_on(
    signal_generator_device: tango.DeviceProxy,
    error_queue: queue.SimpleQueue[tango.DevFailed],
) -> None:
    """
    Set RF output to on.

    :param signal_generator_device: the signal generator Tango device
        under test.
    :param error_queue: a queue for storing errors
    """
    try:
        signal_generator_device.rf_output_on = True
    except tango.DevFailed as dev_failed:
        error_queue.put(dev_failed)


@then("the Signal Generator RF Output field is set to ON")
def check_output_on(
    signal_generator_device: tango.DeviceProxy,
    change_event_callbacks: MockTangoEventCallbackGroup,
) -> None:
    """
    Check that RF output is on.

    :param signal_generator_device: the signal generator Tango device
        under test.
    :param change_event_callbacks: dictionary of mock change event
        callbacks with asynchrony support
    """
    change_event_callbacks["siggen_rf_output_on"].assert_change_event(True)
    assert signal_generator_device.rf_output_on


@scenario(
    "features/signal_generator.feature",
    "Test a Signal Generator output can be turned OFF",
)
def test_sig_gen_set_output_off() -> None:
    """Placeholder for real BDD test."""


@given("the Signal Generator RF Output is ON")
def given_output_on(
    signal_generator_device: tango.DeviceProxy,
    change_event_callbacks: MockTangoEventCallbackGroup,
) -> None:
    """
    Check that the RF output is on.

    :param signal_generator_device: the signal generator Tango device
        under test.
    :param change_event_callbacks: dictionary of mock change event
        callbacks with asynchrony support
    """
    if not signal_generator_device.rf_output_on:
        signal_generator_device.rf_output_on = True
        change_event_callbacks["siggen_rf_output_on"].assert_change_event(True)
        assert signal_generator_device.rf_output_on


@when("the user turns the Signal Generator RF Output OFF")
def set_output_off(
    signal_generator_device: tango.DeviceProxy,
    error_queue: queue.SimpleQueue[tango.DevFailed],
) -> None:
    """
    Set RF output to off.

    :param signal_generator_device: the signal generator Tango device
        under test.
    :param error_queue: a queue for storing errors
    """
    try:
        signal_generator_device.rf_output_on = False
    except tango.DevFailed as dev_failed:
        error_queue.put(dev_failed)


@then("the Signal Generator RF Output field is set to OFF")
def check_rf_output_is_off(
    signal_generator_device: tango.DeviceProxy,
    change_event_callbacks: MockTangoEventCallbackGroup,
) -> None:
    """
    Check that RF output is off.

    :param signal_generator_device: the signal generator Tango device
        under test.
    :param change_event_callbacks: dictionary of mock change event
        callbacks with asynchrony support
    """
    change_event_callbacks["siggen_rf_output_on"].assert_change_event(False)
    assert not signal_generator_device.rf_output_on
