"""Upgrade path test via TMC feature tests."""

import pytest
from pytest_bdd import scenario


@pytest.mark.upgrade_path
@scenario(
    "features/upgradability.feature",
    "Test upgrade path from the current version of SKA Mid running in Production to the current new tag",  # noqa: E501
)
def test_upgrade_path():
    """Validate upgrade path from previous production version."""
