"""Helper functions for interacting with confluence api."""

import re
from pathlib import Path
from typing import Any, cast

from lxml import etree

from .editing import get_page_html_content
from .results.tables import XHTMLTable


def get_template(page_id: str | None | int = None):
    """Get confluence html content template.

    :param page_id: confluence existing page_id, defaults to None
    :type page_id: str | None | int, optional
    :return: etree Element object
    :rtype: etree
    """
    parser = etree.XMLParser(encoding="utf-8", recover=True)
    if page_id:
        data = get_page_html_content(str(page_id))
        return etree.fromstring(data, parser=parser)
    path = Path(__file__).parent.joinpath("template.xhtml")
    with path.open("r", encoding="utf-8") as file:
        return etree.parse(file, parser=parser)


def insert_xhtml_table(template: Any, table: XHTMLTable):
    """Insert html table into a template.

    :param template: confluence existing page template
    :type template: Any
    :param table: html table
    :type table: XHTMLTable
    :return: updated template object
    :rtype: str
    """
    element = table.render_as_xhtml_element()
    if hasattr(template, "getroot"):
        template_root = template.getroot()
    else:
        # we assume it is the root element then
        template_root = template
    results = template_root.findall(f'.//div[@class="{table.table_id}"]')
    if results is None:
        results = template_root.findall(f'.//div[@class="{table.table_id} wrapped"]')
    old_table = results[0]
    parent = old_table.getparent()  # type: ignore
    index = parent.index(old_table)
    parent[index] = element
    result = cast(str, etree.tostring(template, encoding="unicode"))  # type: ignore
    result = re.sub(r"\n+|\s{2,}", "", result)
    return result
