"""."""

import os
import re
from pathlib import Path
from typing import Any, cast

import pytest
from assertpy import assert_that
from lxml import etree

from scripts.confluence.confluence.results import (
    get_results_as_html_table_element,
    get_results_as_html_table_str,
)
from scripts.confluence.confluence.results.file_helper import find_in_test_file


@pytest.fixture(name="expected_results_path")
def fxt_expected_results_path() -> Path:
    """_summary_.

    :return: _description_
    :rtype: Path
    """
    return Path(__file__).parent.joinpath("data/test_results.xhtml")


@pytest.fixture(name="expected_results_object")
def fxt_expected_results_object(expected_results_path: Path):
    """_summary_.

    :param expected_results_path: _description_
    :type expected_results_path: Path
    :return: _description_
    :rtype: _type_
    """
    with expected_results_path.open("r") as file:
        parser1 = etree.XMLParser(encoding="utf-8", recover=True)
        root = etree.parse(file, parser=parser1)
        return root


@pytest.fixture(name="jira_template")
def fxt_jira_template():
    """_summary_.

    :return: _description_
    :rtype: _type_
    """
    path = Path(__file__).parent.joinpath("data/jira_template.xhtml")
    parser = etree.XMLParser(encoding="utf-8", recover=True)
    with path.open("r", encoding="utf-8") as file:
        return etree.parse(file, parser=parser)


@pytest.fixture(name="expected_results")
def fxt_expected_results(expected_results_object: Any):
    """_summary_.

    :param expected_results_object: _description_
    :type expected_results_object: Any
    :return: _description_
    :rtype: _type_
    """
    result = cast(str, etree.tostring(expected_results_object, encoding="unicode"))  # type: ignore
    return re.sub(r"\n+|\s{2,}", "", result)


@pytest.mark.usefixtures("mock_requests")
def test_get_results_as_html_table_str(
    test_data: Path, expected_results: str, expected_results_path: Path
):
    """_summary_.

    :param test_data: _description_
    :type test_data: Path
    :param expected_results: _description_
    :type expected_results: str
    :param expected_results_path: _description_
    :type expected_results_path: Path
    """
    result = get_results_as_html_table_str(test_data)
    if os.getenv("WRITE_RESULTS"):
        with expected_results_path.open("w") as file:
            file.write(result)
    assert_that(result).is_equal_to(expected_results)


def test_get_test_files():
    """_summary_."""
    file = find_in_test_file("test_get_test_files")
    assert_that(file).is_equal_to("tests/unit/confluence/test_confluence_results_loading.py")


@pytest.mark.usefixtures("mock_requests")
def test_get_results_as_html_table(
    test_data: Path, expected_results: str, expected_results_path: Path
):
    """_summary_.

    :param test_data: _description_
    :type test_data: Path
    :param expected_results: _description_
    :type expected_results: str
    :param expected_results_path: _description_
    :type expected_results_path: Path
    """
    result = get_results_as_html_table_element(test_data)
    result = cast(str, etree.tostring(result, encoding="unicode"))  # type: ignore
    result = re.sub(r"\n+|\s{2,}", "", result)
    if os.getenv("WRITE_RESULTS"):
        with expected_results_path.open("w") as file:
            file.write(result)
    assert_that(result).is_equal_to(expected_results)
