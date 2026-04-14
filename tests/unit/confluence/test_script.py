from pathlib import Path
from unittest.mock import patch

import pytest
from assertpy import assert_that

from ska_ser_skallop.confluence.config.implementation import Factory
from ska_ser_skallop.scripts.confluence import upload_to_confluence


@pytest.fixture(name="factory")
def fxt_factory(test_data: Path):
    return Factory(test_data)


@pytest.fixture(name="test_data")
def fxt_test_data() -> Path:
    return Path(__file__).parent.joinpath("data/config.yaml")


@pytest.fixture(name="main_mock_response")
def fxt_test_main_mock_response() -> str:
    return {"message": "Upload to confluence script run successfully."}


@pytest.fixture(name="page_id")
def fxt_page_id() -> int:
    return 232111210


@pytest.fixture(name="test_results")
def fxt_test_results() -> Path:
    return Path(__file__).parent.joinpath("data/cucumber.json")


@pytest.mark.usefixtures("mock_requests")
@patch("ska_ser_skallop.scripts.confluence.upload_to_confluence.main")
def test_confluence_upload_script(main_mock_response):
    assert_that(
        main_mock_response["message"],
        "Upload to confluence script run successfully.",
    )
    assert_that(
        upload_to_confluence.main(),
        "Upload to confluence script run successfully.",
    )
    main_mock_response.assert_called_once()
