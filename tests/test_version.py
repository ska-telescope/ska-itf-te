"""This module tests the ska_ser_test_equipment version."""

import ska_sky_simulator_controller


def test_version() -> None:
    """Test that the ska_sky_simulator_controller version is as expected."""
    assert ska_sky_simulator_controller.__version__ == "0.0.1"
