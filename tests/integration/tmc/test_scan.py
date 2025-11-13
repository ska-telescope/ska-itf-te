"""Telescope scan test feature tests."""

import pytest
from pytest_bdd import scenario


@pytest.mark.hw_in_the_loop
@scenario("features/test_scan.feature", "Perform a scan via TMC")
def test_perform_a_scan_via_tmc():
    """Perform a scan via TMC."""


@pytest.mark.hw_in_the_loop
@scenario(
    "features/test_scan.feature",
    "Perform multiple scans via TMC on the same band releasing"
    " resources and ending the observation only once all scans are complete",
)
def test_perform_multiple_scans_via_tmc_without_reconfiguring():
    """Perform multiple scans via TMC with the same scan config."""


@pytest.mark.hw_in_the_loop
@scenario(
    "features/test_scan.feature",
    "Perform multiple scans via TMC with scan reconfiguration for optional"
    " band switching between scans. Resources are released and the observation"
    " is ended only once all scans are complete.",
)
def test_perform_multiple_scans_via_tmc_reconfiguring_between_scans():
    """Perform multiple scans via TMC with interchanging between band 1 and band 2."""
