"""Configure scan via TMC feature tests."""

import os

import pytest
from pytest_bdd import scenario, then
from tango import DevState

# TODO: Rethink usage of globals like this
SUT_NAMESPACE = os.getenv("KUBE_NAMESPACE")


@scenario(
    "features/tmc_end_to_end.feature",
    "End to End signal chain verification via TMC",
)
def test_e2e_via_tmc():
    """."""


@pytest.mark.hw_in_the_loop
@scenario(
    "features/tmc_end_to_end.feature",
    "End to End signal chain verification via TMC - With HW",
)
def test_e2e_via_tmc_slow():
    """."""
    global SUT_NAMESPACE

    if not (SUT_NAMESPACE := os.getenv("E2E_TEST_EXECUTION_NAMESPACE")):
        SUT_NAMESPACE = os.getenv("KUBE_NAMESPACE")


@pytest.mark.hw_in_the_loop
@scenario(
    "features/tmc_end_to_end.feature",
    "End to End signal chain verification via TMC with BITE data",
)
def test_e2e_via_tmc_slow_with_bite():
    """."""
    global SUT_NAMESPACE

    if not (SUT_NAMESPACE := os.getenv("E2E_TEST_EXECUTION_NAMESPACE")):
        SUT_NAMESPACE = os.getenv("KUBE_NAMESPACE")


@then("the telescope is in the OFF state")
def _(telescope_handlers):
    """Check that the telescope is in the OFF state.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    """
    tmc, _, _, _ = telescope_handlers

    tmc_central_node = tmc.central_node

    assert tmc_central_node.telescopeState in [DevState.OFF, DevState.UNKNOWN]
