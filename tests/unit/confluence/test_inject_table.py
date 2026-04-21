"""."""

import os
import re
from pathlib import Path
from typing import Any, cast

import pytest
from assertpy import assert_that
from lxml import etree

from scripts.confluence.confluence.helper import get_template, insert_xhtml_table

from .conftest import XHTMLTable


@pytest.fixture(name="page")
def fxt_page():
    """_summary_.

    :return: _description_
    :rtype: _type_
    """
    return get_template()


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


def test_inject_table(
    page: Any,
    results_table: XHTMLTable,
    expected_results: str,
    expected_results_path: Path,
):
    """_summary_.

    :param page: _description_
    :type page: Any
    :param results_table: _description_
    :type results_table: XHTMLTable
    :param expected_results: _description_
    :type expected_results: str
    :param expected_results_path: _description_
    :type expected_results_path: Path
    """
    result = insert_xhtml_table(page, results_table)
    if os.getenv("WRITE_RESULTS"):
        with expected_results_path.open("w") as file:
            file.write(result)
    assert_that(result).is_equal_to(expected_results)
