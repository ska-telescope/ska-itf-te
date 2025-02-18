"""Telescope scan test feature tests."""

from pytest_bdd import scenario


@scenario("features/test_scan.feature", "Perform a scan via TMC")
def test_perform_a_scan_via_tmc():
    """Perform a scan via TMC."""
