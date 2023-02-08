"""This module tests the ska_ser_test_equipment version."""

import ska_skysim_controller


def test_version() -> None:
    """Test that the ska_skysim_controller version is as expected."""
    assert ska_skysim_controller.__version__ == "0.0.1"
