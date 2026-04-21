"""."""

from .results import (
    get_results_as_html_table,
    get_results_as_html_table_element,
    get_results_as_html_table_str,
)
from .tables import XHTMLTable

__all__ = [
    "get_results_as_html_table_str",
    "get_results_as_html_table_element",
    "get_results_as_html_table",
    "XHTMLTable",
]
