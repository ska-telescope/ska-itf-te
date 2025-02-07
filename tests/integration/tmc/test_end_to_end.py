"""Configure scan via TMC feature tests."""

import json
import logging
import os
import sys
from time import sleep

import pytest
from pytest_bdd import parsers, scenario, then, when
from ska_control_model import ObsState
from tango import DevState

from tests.integration.tmc.conftest import wait_for_event
from utils.enums import DishMode

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), ".jupyter-notebooks")))
from src.notebook_tools import generate_fsp  # noqa: E402

# TODO: Rethink usage of globals like this
CLUSTER_DOMAIN = "miditf.internal.skao.int"
SUT_NAMESPACE = os.getenv("KUBE_NAMESPACE")
DATA_DIR = ".jupyter-notebooks/data/mid_telescope"
TMC_CONFIGS = f"{DATA_DIR}/tmc"
expected_k_value = 1
logger = logging.getLogger()
OVERRIDE_SCAN_DURATION = os.getenv("OVERRIDE_SCAN_DURATION")
OVERRIDE_SCAN_BAND = os.getenv("OVERRIDE_SCAN_BAND")
INTEGRATION_FACTOR = os.getenv("INTEGRATION_FACTOR")


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


@when("I turn OFF the telescope")
def _(telescope_handlers, receptor_ids):
    """Turn the telescope OFF via TMC.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    :param receptor_ids: _description_
    :type receptor_ids: _type_
    """
    logger.info("Turning OFF the telescope")

    tmc, _, _, _ = telescope_handlers
    RECEPTORS = receptor_ids

    tmc_central_node = tmc.central_node

    tmc_central_node.TelescopeOff()

    for receptor in RECEPTORS:
        wait_for_event(tmc.get_dish_leaf_node_dp(receptor), "dishMode", DishMode.STANDBY_LP)

    wait_for_event(tmc_central_node, "telescopeState", DevState.OFF)


@then("the telescope is in the OFF state")
def _(telescope_handlers):
    """Check that the telescope is in the OFF state.

    :param telescope_handlers: _description_
    :type telescope_handlers: _type_
    """
    tmc, _, _, _ = telescope_handlers

    tmc_central_node = tmc.central_node

    assert tmc_central_node.telescopeState in [DevState.OFF, DevState.UNKNOWN]


@then("the respective dataproducts are available on the DPD")
def _(pb_and_eb_ids):
    """Check that the respective dataproducts are available on the DPD via the dataproducts API.

    :param pb_and_eb_ids: _description_
    :type pb_and_eb_ids: _type_
    """
    # TODO: Implement
    pb_id, eb_id = pb_and_eb_ids

    assert True
