"""
Script for updating Confluence pages with configuration diagrams and test results.

This script reads a configuration file and test results file, generates diagrams from the config,
and updates an existing Confluence page with the diagrams as attachments and test results as a
table.

Command-line Arguments:
    config (Path): The configuration file representing the configuration item.
    results (Path): The test results file (e.g. cucumber.json).

Environment Variables:
    PAGE_ID (str): The Confluence page ID to update. Defaults to "232111210".
"""

import argparse
import os
from pathlib import Path

from scripts.confluence.confluence import (
    generate_diagrams_from_config,
    get_attachment_data,
    get_results_as_html_table,
    get_template,
    insert_xhtml_table,
    update_attachment_by_id,
    update_page_content,
)

parser = argparse.ArgumentParser(
    description="Update an existing confluence page from config and test results"
)
parser.add_argument(
    "config",
    metavar="configfile",
    type=Path,
    help="The configuration file representing the configuration item",
)
parser.add_argument(
    "results",
    metavar="resultsfile",
    type=Path,
    help="the test results file (e.g. cucumber.json)",
)

PAGE_ID = os.getenv("PAGE_ID", "232111210")


def main():
    """."""
    args = parser.parse_args()
    config = args.config
    results = args.results
    diagrams = generate_diagrams_from_config(config)  # type: ignore
    attachments = get_attachment_data(page_id=PAGE_ID)
    if diagrams.dependency_diagram_size != attachments["dependencies.png"]["file_size"]:
        attachment_id = attachments["dependencies.png"]["id"]
        test_image_path = diagrams.dependency_diagram
        update_attachment_by_id(page_id=PAGE_ID, attachment_id=attachment_id, path=test_image_path)
    if diagrams.platform_diagram_size != attachments["platform.png"]["file_size"]:
        attachment_id = attachments["platform.png"]["id"]
        test_image_path = diagrams.platform_diagram
        update_attachment_by_id(page_id=PAGE_ID, attachment_id=attachment_id, path=test_image_path)
    # get results
    table = get_results_as_html_table(results)
    template = get_template(PAGE_ID)
    updated = insert_xhtml_table(template, table)
    update_page_content(PAGE_ID, updated)
