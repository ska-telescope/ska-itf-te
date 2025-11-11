"""Set of tests which validate TMC commands individually."""

import pytest
from pytest_bdd import scenario


@pytest.mark.hw_in_the_loop
@scenario("features/test_individual_commands.feature", "Assign resources")
def test_assign_resources_via_tmc():
    """Assign resources via TMC."""


@pytest.mark.hw_in_the_loop
@scenario("features/test_individual_commands.feature", "Configure scan")
def test_configure_scan_via_tmc():
    """Configure scan via TMC."""


@pytest.mark.hw_in_the_loop
@scenario("features/test_individual_commands.feature", "Scan")
def test_scan_via_tmc():
    """Scan via TMC."""


@pytest.mark.hw_in_the_loop
@scenario("features/test_individual_commands.feature", "End the observation")
def test_end_observation_via_tmc():
    """End the observation via TMC."""


@pytest.mark.hw_in_the_loop
@scenario("features/test_individual_commands.feature", "Release resources")
def test_release_resources_via_tmc():
    """Release resources via TMC."""
