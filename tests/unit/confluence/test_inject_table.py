import os
import re
from pathlib import Path
from typing import Any, cast

import pytest
from assertpy import assert_that
from lxml import etree

from ska_ser_skallop.confluence.helper import get_template, insert_xhtml_table

from .conftest import XHTMLTable


@pytest.fixture(name="page")
def fxt_page():
    return get_template()


@pytest.fixture(name="expected_results_object")
def fxt_expected_results_object(expected_results_path: Path):
    with expected_results_path.open("r") as file:
        parser1 = etree.XMLParser(encoding="utf-8", recover=True)
        root = etree.parse(file, parser=parser1)
        return root


@pytest.fixture(name="expected_results")
def fxt_expected_results(expected_results_object: Any):
    result = cast(str, etree.tostring(expected_results_object, encoding="unicode"))  # type: ignore
    return re.sub(r"\n+|\s{2,}", "", result)


def test_inject_table(
    page: Any,
    results_table: XHTMLTable,
    expected_results: str,
    expected_results_path: Path,
):
    result = insert_xhtml_table(page, results_table)
    if os.getenv("WRITE_RESULTS"):
        with expected_results_path.open("w") as file:
            file.write(result)
    assert_that(result).is_equal_to(expected_results)
