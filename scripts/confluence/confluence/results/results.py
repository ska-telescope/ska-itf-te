"""_summary_."""

from functools import reduce
from pathlib import Path

from .factory import get_results
from .items import Feature, XRayTest
from .tables import XHTMLTable


def _aggegate_scenarios(current: list[XRayTest], new: list[XRayTest]) -> list[XRayTest]:
    return [*current, *new]


def get_results_as_html_table(path: Path):
    """_summary_.

    :param path: _description_
    :type path: Path
    :return: _description_
    :rtype: _type_
    """
    results: list[Feature] = get_results(path)
    scenarios = reduce(_aggegate_scenarios, [feature.tests for feature in results], [])
    return XHTMLTable(scenarios)


def get_results_as_html_table_str(path: Path):
    """_summary_.

    :param path: _description_
    :type path: Path
    :return: _description_
    :rtype: _type_
    """
    table = get_results_as_html_table(path)
    return table.render()


def get_results_as_html_table_element(path: Path):
    """_summary_.

    :param path: _description_
    :type path: Path
    :return: _description_
    :rtype: _type_
    """
    table = get_results_as_html_table(path)
    return table.render_as_xhtml_element()
