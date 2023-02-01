"""This module contains BBD tests for Spectrum Analyser scenarios."""
# import pytest
from pytest_bdd import given, parsers, scenario, then, when


@scenario(
    "features/spectrum_analyser.feature",
    "Test that a Spectrum Analyser can be configured to plot a trace",
)
def test_spectrum_analyser_configuration() -> None:
    """Test that a Spectrum Analyser can be configured to plot a trace."""


@given("the Spectrum Analyser is initialised")
def spectrum_analyser_initialise() -> None:
    """Initialise the Spectrum Analyser."""
    # TODO


@given("the Spectrum Analyser is online")
def spectrum_analyser_connect() -> None:
    """Connect to the Spectrum Analyser."""
    # TODO


@when(
    parsers.parse(
        "the user sets the Spec Analyser start freq as {start_freq} Hz"
    )
)
def set_spectrum_analyser_start_frequency() -> None:
    """
    Set the Spectrum Analyser start frequency as.

    <start_frequency> Hz.
    """
    # TODO


@when(
    parsers.parse(
        "the user sets the Spec Analyser stop freq as {stop_freq} Hz"
    )
)
def set_spectrum_analyser_stop_frequency() -> None:
    """
    Set the Spectrum Analyser stop frequency as.

    <stop_frequency> Hz.
    """
    # TODO


@then(parsers.parse("the Spec Analyser start freq is set to {start_freq} Hz"))
def check_spectrum_analyser_start_frequency() -> None:
    """Check the specified start frequency for the Spectrum Analyser is set."""
    # TODO


@then(parsers.parse("the Spec Analyser stop freq is set to {stop_freq} Hz"))
def check_spectrum_analyser_stop_frequency() -> None:
    """Check the specified stop frequency for the Spectrum Analyser is set."""
    # TODO
