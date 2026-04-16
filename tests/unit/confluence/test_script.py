"""."""

from pathlib import Path
from unittest.mock import patch

import pytest
from assertpy import assert_that

from scripts.confluence import upload_to_confluence
from scripts.confluence.confluence.config.implementation import Factory


@pytest.fixture(name="factory")
def fxt_factory(test_data: Path):
    """_summary_.

    :param test_data: _description_
    :type test_data: Path
    :return: _description_
    :rtype: _type_
    """
    return Factory(test_data)


@pytest.fixture(name="test_data")
def fxt_test_data() -> Path:
    """_summary_.

    :return: _description_
    :rtype: Path
    """
    return Path(__file__).parent.joinpath("data/config.yaml")


@pytest.fixture(name="main_mock_response")
def fxt_test_main_mock_response() -> str:
    """_summary_.

    :return: _description_
    :rtype: str
    """
    return {"message": "Upload to confluence script run successfully."}


@pytest.fixture(name="page_id")
def fxt_page_id() -> int:
    """_summary_.

    :return: _description_
    :rtype: int
    """
    return 232111210


@pytest.fixture(name="test_results")
def fxt_test_results() -> Path:
    """_summary_.

    :return: _description_
    :rtype: Path
    """
    return Path(__file__).parent.joinpath("data/cucumber.json")


@pytest.mark.usefixtures("mock_requests")
@patch("scripts.confluence.upload_to_confluence.main")
def test_confluence_upload_script(main_mock_response):
    """_summary_.

    :param main_mock_response: _description_
    :type main_mock_response: _type_
    """
    assert_that(
        main_mock_response["message"],
        "Upload to confluence script run successfully.",
    )
    assert_that(
        upload_to_confluence.main(),
        "Upload to confluence script run successfully.",
    )
    main_mock_response.assert_called_once()
