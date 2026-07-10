"""Upgrade path test via TMC feature tests."""

# import pytest
from pytest_bdd import scenario


# @pytest.mark.hw_in_the_loop
@scenario(
    "features/upgradability.feature",
    "Test upgrade path from the current version of SKA Mid running in Production to the current new tag",
)
def test_upgrade_path():
    """."""
