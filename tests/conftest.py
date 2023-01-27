"""This module contains test harness elements common to all unit tests."""
import logging
from typing import Dict

import pytest
from ska_tango_testing.mock import MockCallable, MockCallableGroup


def pytest_itemcollected(item: pytest.Item) -> None:
    """
    Modify a test after it has been collected by pytest.

    This hook implementation adds the "forked" custom mark to all tests
    that use the `signal_generator_device` fixture, causing them to be
    sandboxed in their own process.

    :param item: the collected test for which this hook is called
    """
    fixture_names = item.fixturenames  # type: ignore[attr-defined]
    if (
        "signal_generator_device" in fixture_names
        or "spectrum_analyser_device" in fixture_names
    ):
        item.add_marker("forked")


@pytest.fixture()
def logger() -> logging.Logger:
    """
    Fixture that returns a default logger.

    The logger will be set to DEBUG level, as befits testing.

    :return: a logger
    """
    debug_logger = logging.getLogger()
    debug_logger.setLevel(logging.DEBUG)
    return debug_logger


@pytest.fixture(name="callbacks")
def fixture_callbacks() -> MockCallableGroup:
    """
    Return a dictionary of callbacks with asynchrony support.

    :return: a collections.defaultdict that returns callbacks by name.
    """
    return MockCallableGroup(
        "communication_status",
        "component_state",
        "task",
        timeout=5.0,
    )


@pytest.fixture(name="communication_status_callback")
def fixture_communication_status_callback(
    callbacks: MockCallableGroup,
) -> MockCallableGroup._Callable:
    """
    Return a mock callback with asynchrony support.

    This mock callback can be registered with the component manager, so
    that it is called when the status of communication with the
    component changes.

    :param callbacks: a dictionary from which callbacks with asynchrony
        support can be accessed.

    :return: a callback with asynchrony support
    """
    return callbacks["communication_status"]


@pytest.fixture(name="component_state_callback")
def fixture_component_state_callback(
    callbacks: Dict[str, MockCallable]
) -> MockCallable:
    """
    Return a mock callback with asynchrony support.

    This mock callback can be registered with the component manager, so
    that it is called when the state of the component changes.

    :param callbacks: a dictionary from which callbacks with asynchrony
        support can be accessed.

    :return: a callback with asynchrony support
    """
    return callbacks["component_state"]


@pytest.fixture(name="task_callback")
def fixture_task_callback(callbacks: Dict[str, MockCallable]) -> MockCallable:
    """
    Return a mock callback with asynchrony support.

    This mock callback is intended to be passed to a long-running
    command as a task callback.

    :param callbacks: a dictionary from which callbacks with asynchrony
        support can be accessed.

    :return: a callback with asynchrony support
    """
    return callbacks["task"]
