"""."""

import os
from pathlib import Path
from typing import Any

import pytest
from assertpy import add_extension
from lxml import etree

from scripts.confluence.confluence.results import XHTMLTable, get_results_as_html_table
from scripts.confluence.confluence.results.jira_helper import mock_requests


def is_the_same_element_as(self: Any, other: str, write: str | None = None):
    """_summary_.

    :param self: _description_
    :type self: Any
    :param other: _description_
    :type other: str
    :param write: _description_, defaults to None
    :type write: str | None, optional
    """
    parser = etree.XMLParser(encoding="utf-8", recover=True)
    self_as_element = etree.fromstring(self.val, parser=parser)
    other_as_element = etree.fromstring(other, parser=parser)
    self_as_element_str = etree.tostring(self_as_element, encoding="unicode")  # type: ignore
    other_as_element_str = etree.tostring(other_as_element, encoding="unicode")  # type: ignore
    if self_as_element_str != other_as_element_str:
        if write is not None:
            with open(f"expected.{write}", "w", encoding="utf-8") as file:
                file.write(other_as_element_str)  # type: ignore
            with open(f"actual.{write}", "w", encoding="utf-8") as file:
                file.write(self_as_element_str)  # type: ignore
        self.error(f"{self_as_element_str} is not equal to {other_as_element_str}")


add_extension(is_the_same_element_as)


@pytest.fixture(name="test_data")
def fxt_test_data() -> Path:
    """_summary_.

    :return: _description_
    :rtype: Path
    """
    return Path(__file__).parent.joinpath("data/cucumber.json")


def _issue(_id: str):
    if _id == "4567":
        inner = {
            "fields": {
                "issuelinks": [
                    {
                        "outwardIssue": {
                            "id": "8910",
                            "fields": {
                                "issuetype": {"name": "Requirement"},
                            },
                        },
                        "type": {"name": "Tests"},
                        "id": "1235",
                    }
                ],
            }
        }
    elif _id == "8910":
        inner = {
            "fields": {
                "customfield_12133": "SKAO-TM_REQ-706",
                "customfield_13903": "https://skaoffice.jamacloud.com/"
                "perspective.req?projectId=335&amp;docId=1056423",
            }
        }
    elif _id == "4321":
        inner = {"fields": {}}
    else:
        inner = {}
    return {**{"id": _id}, **inner}


@pytest.fixture(name="mock_requests")
def fxt_mock_requests():
    """_summary_.

    :yields: None
    """
    mock_responses = {
        "XTP-4506": _issue("1234"),
        "XTP-20083": _issue("0000"),
        "XTP-14873": _issue("0000"),
        "XTP-4593": _issue("0000"),
        "XTP-4774": _issue("0000"),
        "XTP-16344": _issue("0000"),
        "XTP-3958": _issue("0000"),
        "XTP-16343": _issue("0000"),
        "1234": _issue("4567"),
        "8910": _issue("8910"),
        "0000": _issue("4321"),
    }
    with mock_requests(mock_responses):
        os.environ["JIRA_USERNAME"] = "mock_username"
        os.environ["JIRA_PASSWORD"] = "mock_password"
        yield


@pytest.fixture(name="results_table")
def fxt_results_table(mock_requests: None, test_data: Path) -> XHTMLTable:
    """_summary_.

    :param mock_requests: _description_
    :type mock_requests: None
    :param test_data: _description_
    :type test_data: Path
    :return: _description_
    :rtype: XHTMLTable
    """
    return get_results_as_html_table(test_data)


@pytest.fixture(name="expected_results_path")
def fxt_expected_results_path() -> Path:
    """_summary_.

    :return: _description_
    :rtype: Path
    """
    return Path(__file__).parent.joinpath("data/expected_page.xhtml")
