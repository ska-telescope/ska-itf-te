"""This module defines the --xray-ids option and its behaviour."""

import functools
from typing import List, Set, TypedDict

import logging
import pytest

from ska_ser_test_equipment.scpi import (
    InterfaceDefinitionFactory,
    InterfaceDefinitionType,
    SupportedProtocol,
)

InstrumentInfoType = TypedDict(
    "InstrumentInfoType",
    {
        "protocol": SupportedProtocol,
        "host": str,
        "port": int,
        "simulator": bool,
    },
)


# TODO: https://github.com/pytest-dev/pytest-forked/issues/67
# We're stuck on pytest 6.2 until this gets fixed, and this version of
# pytest is not fully typehinted
def pytest_addoption(parser) -> None:  # type: ignore[no-untyped-def]
    """
    Implement  the `--xray-ids` option.

    Restricts the set of tests to only those marked with xray(JIRA_ID),
    where JIRA_ID is one of the specified comma-separated IDs.

    It would be nice to upstream this to pytest-jira-xray...

    :param parser: the command line options parser
    """
    xray = parser.getgroup("Jira Xray report")
    xray.addoption(
        "--xray-ids",
        action="store",
        type=functools.partial(str.split, sep=","),
        metavar="JIRA_ID[,...]",
        help="only run tests marked with the specified Jira IDs",
    )


# TODO: https://github.com/pytest-dev/pytest-forked/issues/67
# We're stuck on pytest 6.2 until this gets fixed, and this version of
# pytest is not fully typehinted
def pytest_collection_modifyitems(  # type: ignore[no-untyped-def]
    config, items: List[pytest.Item]
) -> None:
    """
    Handle our custom --xray-ids option.

    For each test, get the id args passed to all xray markers. Only
    include the test if at least one of the ids appears in --xray-ids.

    :param config: the pytest config object
    :param items: list of tests collected by pytest
    """

    def xray_ids(test: pytest.Item) -> Set[str]:
        return {m.args[0] for m in test.iter_markers(name="xray")}

    target_ids = config.getoption("--xray-ids")
    if target_ids:
        items[:] = [i for i in items if xray_ids(i).intersection(target_ids)]


@pytest.fixture()
def interface_definition(model: str) -> InterfaceDefinitionType:
    """
    Return the SCPI interface definition for an instrument model.

    :param model: the name of the instrument model.

    :return: the SCPI interface definition
    """
    logging.info("Get interface definition for %s", model)
    return InterfaceDefinitionFactory()(model)
