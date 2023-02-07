"""This module tests the ska_ser_test_equipment version."""

from pytest_bdd import given, parsers, scenario, then

from ska_sky_simulator_controller import __version__ as version


@scenario("features/version.feature", "Test version of skysimctl package")
def test_version_of_skysimctl_package():
    """Test version of skysimctl package."""


@given("an imported ska_sky_simulator_controller package")
def imported_package():
    """Fails if there is no imported ska_sky_simulator_controller package."""
    print(version)


@then(parsers.parse("its version is {test_version}"))
def check_version(test_version):
    """
    Package version is 0.1.0.

    :param version: the version of the imported package - see Jira issue.
    """
    assert version == test_version
