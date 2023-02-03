"""This module tests the ska_ser_test_equipment version."""

import ska_ser_test_equipment


def test_version() -> None:
    """Test that the ska_ser_test_equipment version is as expected."""
    assert ska_ser_test_equipment.__version__ == "0.6.2"
