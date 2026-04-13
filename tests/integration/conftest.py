"""pytest global settings, fixtures and global bdd step implementations for integration tests."""

import logging
import os
from typing import Any, Callable

import pytest

from pytest_bdd import given
from pytest_bdd.parser import Feature, Scenario, Step
from tango import DeviceProxy

from tests.integration.tmc.conftest import TMC


logger = logging.getLogger(__name__)


def pytest_bdd_before_step_call(
    request: Any,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable[[Any], Any],
    step_func_args: dict[str, Any],
):
    """_summary_.

    :param request: _description_
    :type request: Any
    :param feature: _description_
    :type feature: Feature
    :param scenario: _description_
    :type scenario: Scenario
    :param step: _description_
    :type step: Step
    :param step_func: _description_
    :type step_func: Callable[[Any], Any]
    :param step_func_args: _description_
    :type step_func_args: dict[str, Any]
    """
    if os.getenv("SHOW_STEP_FUNCTIONS"):
        logger.info(
            "\n**********************************************************\n"
            f"***** {step.keyword} {step.name} *****\n"
            "**********************************************************"
        )

    @property
    def nr_of_receptors(self):
        """_summary_.

        :return: _description_
        :rtype: _type_
        """
        return self._nr_of_receptors

    @nr_of_receptors.setter
    def nr_of_receptors(self, value: int):
        """_summary_.

        :param value: _description_
        :type value: int
        """
        self._nr_of_receptors = value
        self._receptors = [  # pylint: disable=unnecessary-comprehension
            i for i in range(1, value + 1)
        ]

    @property
    def receptors(self):
        """_summary_.

        :return: _description_
        :rtype: _type_
        """
        return self._receptors

    @receptors.setter
    def receptors(self, receptor: list[int]):
        """_summary_.

        :param receptor: _description_
        :type receptor: list[int]
        """
        self._receptors = receptor


@given("a mid telescope")
@given("a TMC")
def a_tmc(receptor_ids):
    """Given a TMC.

    :param receptor_ids: ids of the receptors available
    :type receptor_ids: List of dish ids
    """
    tmc = TMC()
    sdp_subarray_leaf_node = tmc.sdp_subarray_leaf_node
    csp_subarray_leaf_node = tmc.csp_subarray_leaf_node

    tmc_central_node = tmc.central_node
    result = tmc_central_node.ping()
    assert result > 0

    tmc_subarray_node1 = tmc.subarray_node
    result = tmc_subarray_node1.ping()
    assert result > 0

    csp_master_leaf_node = tmc.csp_master_leaf_node
    result = csp_master_leaf_node.ping()
    assert result > 0

    sdp_master_leaf_node = tmc.sdp_master_leaf_node
    result = sdp_master_leaf_node.ping()
    assert result > 0

    csp_subarray_leaf_node = tmc.csp_subarray_leaf_node
    result = csp_subarray_leaf_node.ping()
    assert result > 0

    sdp_subarray_leaf_node = tmc.sdp_subarray_leaf_node
    result = sdp_subarray_leaf_node.ping()
    assert result > 0

    receptors = receptor_ids
    for receptor in receptors:
        dish_leaf_node = tmc.get_dish_leaf_node_dp(receptor)
        logger.info("Dish Leaf Node devname: %s", dish_leaf_node.dev_name())
        result = dish_leaf_node.ping()
        assert result > 0


@given("an alarm handler")
def a_alarm_handler():
    """Given an alarm handler."""
    alarm_handler = DeviceProxy("alarm/handler/01")
    result = alarm_handler.ping()
    result > 0


class ResponseData(object):
    """Class to have response data received."""

    def __init__(self) -> None:
        """Initialise class variables."""
        self.response = {}
        self.alarm_handler_device = DeviceProxy("alarm/handler/01")

    def clear_alarms(self):
        """Clear the configured alarms."""
        if self.response:
            if self.response.get("alarm_summary"):
                for tag in self.response["alarm_summary"]["tag"]:
                    self.alarm_handler_device.Remove(tag)
                assert self.alarm_handler_device.alarmList == ()


@pytest.fixture(name="response_data")
def fixture_default_response():
    """Set up default responce.

    :yield: A class object representing default response for the system under test.
    """
    response_data = ResponseData()
    yield response_data
    response_data.clear_alarms()


class AlarmHandlerTestContext:
    """Class to store the alarm handler test context."""


@pytest.fixture
def alarm_handler_test_context():
    """Fixture to manage alarm handler test context.

    :yield: AlarmHandlerTestContext class instance to store shared data.

    """
    test_context = AlarmHandlerTestContext()
    yield test_context
