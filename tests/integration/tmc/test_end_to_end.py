"""Configure scan via TMC feature tests."""

import os

import pytest
from pytest_bdd import scenario, then
from ska_control_model._dev_state import DevState

from utils.enums import DishMode
from utils.telescope_teardown import TelescopeHandler, TelescopeState

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


@pytest.mark.hw_in_the_loop
@scenario(
    "features/tmc_end_to_end.feature",
    "End to End signal chain verification via TMC without telescope OFF",
)
def test_e2e_via_tmc_slow_without_off():
    """."""
    global SUT_NAMESPACE

    if not (SUT_NAMESPACE := os.getenv("E2E_TEST_EXECUTION_NAMESPACE")):
        SUT_NAMESPACE = os.getenv("KUBE_NAMESPACE")


@then("the telescope is in the released-resources state")
def _(settings, receptor_ids):
    """Check that the telescope is in the released-resources state.

    :param settings: _description_
    :type settings: _type_
    :param receptor_ids: _description_
    :type receptor_ids: _type_
    """
    base_dish_states_operate = {receptor_id: DishMode.OPERATE for receptor_id in receptor_ids}

    released_resources_state = TelescopeState(
        dishes=base_dish_states_operate,
        central_node=DevState.ON,
    )

    # Due to known issue with state aggregation for telescopeState
    released_resources_state_central_node_unknown = TelescopeState(
        dishes=base_dish_states_operate,
        central_node=DevState.UNKNOWN,
    )

    telescope_handler = TelescopeHandler(
        settings["SUT_namespace"], settings["sut_cluster_domain"], receptor_ids
    )

    current_telescope_state = telescope_handler.get_current_state()

    valid_released_resources_states = [
        released_resources_state,
        released_resources_state_central_node_unknown,
    ]

    assert current_telescope_state in valid_released_resources_states


@then("the telescope is in the OFF state")
def _(settings, receptor_ids):
    """Check that the telescope is in the OFF state.

    :param settings: _description_
    :type settings: _type_
    :param receptor_ids: _description_
    :type receptor_ids: _type_
    """
    base_dish_states_standby_lp = {
        receptor_id: DishMode.STANDBY_LP for receptor_id in receptor_ids
    }

    off_state_1 = TelescopeState(dishes=base_dish_states_standby_lp)

    # Due to known issue with state aggregation for telescopeState
    off_state_2 = TelescopeState(dishes=base_dish_states_standby_lp, central_node=DevState.UNKNOWN)

    telescope_handler = TelescopeHandler(
        settings["SUT_namespace"], settings["sut_cluster_domain"], receptor_ids
    )
    current_telescope_state = telescope_handler.get_current_state()

    assert current_telescope_state in [off_state_1, off_state_2]
