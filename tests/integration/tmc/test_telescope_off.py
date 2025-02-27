"""Telescope OFF test feature tests."""

import pytest
from pytest_bdd import scenario, then
from tango import DevState


@pytest.mark.hw_in_the_loop
@scenario("features/test_telescope_off.feature", "Telescope OFF via TMC")
def test_telescope_off_via_tmc():
    """Telescope ON via TMC."""


@then("the telescope is in the OFF state")
def _(telescope_handlers):
    """Telescope is in the OFF state.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    """
    tmc, _, _, _ = telescope_handlers
    assert tmc.central_node.telescopeState == DevState.OFF
