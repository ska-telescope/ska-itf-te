"""Telescope scan test feature tests."""

import pytest
from pytest_bdd import scenario


@pytest.mark.hw_in_the_loop
@scenario("features/test_scan.feature", "Perform a scan via TMC")
def test_perform_a_scan_via_tmc():
    """Perform a scan via TMC."""
