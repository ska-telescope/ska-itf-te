import json
import os
import re
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
from assertpy import assert_that

from scripts.confluence.confluence.editing import (
    Attachment,
    ConfluenceConnection,
    get_attachment_data,
    get_page_attachments,
    get_page_html_content,
    get_page_meta_data,
    get_requests_api,
    mock_api,
    update_attachment_by_id,
    update_page_content,
)

# https://confluence.skatelescope.org/display/SE/Mid+ITF+Configuration+and+Test+Results
PAGE_ID = 232111210


@pytest.fixture(name="page_id")
def fxt_page_id() -> int:
    return PAGE_ID


@pytest.mark.usefixtures("mock_requests")
def test_update_page_content(page_id: int, expected_results_path: Path):
    response = update_page_content(page_id, expected_results_path)
    assert_that(response.status_code).is_equal_to(200)


@pytest.fixture(name="html_content_path")
def fxt_html_content_path(tmp_path: Path):
    if os.getenv("USE_LOCAL"):
        return Path("html_temp.xhtml")
    return tmp_path.joinpath("html_temp.txt")


@pytest.mark.usefixtures("mock_requests")
def test_get_page_html_content(
    page_id: int, html_content_path: Path, expected_get_contents_response: str
):
    results = get_page_html_content(page_id, html_content_path)
    assert_that(results).is_equal_to(expected_get_contents_response, write="xhtml")


@pytest.mark.usefixtures("mock_requests")
def test_get_page_attachments(
    expected_dependency_title: str, expected_dependency_attachment: Attachment
):
    page_attachment = get_page_attachments(PAGE_ID, expected_dependency_title)
    assert_that(page_attachment).is_equal_to(expected_dependency_attachment)


@pytest.fixture(name="metadata_path")
def fxt_metadata_path(tmp_path: Path):
    if os.getenv("USE_LOCAL"):
        return Path("temp-metadata.json")
    return tmp_path.joinpath("temp-metadata.json")


@pytest.fixture(name="get_metadata_response")
def fxt_get_metadata_response() -> dict[str, Any]:
    path = Path(__file__).parent.joinpath("data/expected_metadata.json")
    with path.open(encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture(name="expected_get_metadata_response")
def fxt_expected_get_metadata_response(get_metadata_response: dict[str, Any]):
    data = json.dumps(get_metadata_response)
    return sha256(data.encode()).hexdigest()


@pytest.fixture(name="mock_get_contents_id")
def fxt_mock_get_contents_id(page_id: str):
    return f"{page_id}expand_body.storage"


@pytest.fixture(name="get_contents_response")
def fxt_get_contents_response():
    path = Path(__file__).parent.joinpath("data/expected_page.xhtml")
    with path.open(encoding="utf-8") as file:
        return file.read()


@pytest.fixture(name="expected_get_contents_response")
def fxt_expected_get_contents_response(get_contents_response: str):
    return get_contents_response
    # return "be7b858f23e3fffe5462e70438254563c21bdea71e453cb0eb389e2c226c4328"


@pytest.fixture(name="mock_put_contents_id")
def fxt_mock_put_contents_id(page_id: str):
    return f"{page_id}expand_body.storage"


@pytest.fixture(name="mock_get_attachments_results")
def fxt_mock_get_attachments_results():
    path = Path(__file__).parent.joinpath("data/expected_attachment_results.json")
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture(name="mock_get_attachments_key")
def fxt_mock_get_attachments_key(page_id: int):
    return f"{page_id}child_attachment"


@pytest.fixture(name="mock_gets")
def fxt_mock_gets(
    page_id: int,
    get_metadata_response: dict[str, Any],
    mock_get_contents_id: str,
    get_contents_response: str,
    mock_get_attachments_key: str,
    mock_get_attachments_results: dict[str, Any],
):
    return {
        str(page_id): get_metadata_response,
        mock_get_contents_id: get_contents_response,
        mock_get_attachments_key: mock_get_attachments_results,
    }


@pytest.fixture(name="put_contents_response")
def fxt_put_contents_response() -> dict[str, Any]:
    return {}


@pytest.fixture(name="mock_puts")
def fxt_mock_puts(
    mock_put_contents_id: str,
    put_contents_response: dict[str, Any],
):
    return {mock_put_contents_id: put_contents_response}


@pytest.fixture(name="mock_posts")
def fxt_mock_posts(
    page_id: int,
    mock_get_attachments_key: str,
) -> dict[str, Any]:
    return {
        str(page_id): {},
        mock_get_attachments_key: {},
    }


@pytest.fixture(name="mock_requests")
def fxt_mock_requests(
    mock_gets: dict[str, Any],
    mock_puts: dict[str, Any],
    mock_posts: dict[str, Any],
):
    if not os.getenv("DISABLE_MOCKING"):
        os.environ["CONFLUENCE_HOST"] = "dummy"
        os.environ["CONFLUENCE_SERVICE_ACCOUNT_TOKEN"] = "dummy"
        os.environ["CONFLUENCE_SERVICE_ACCOUNT_USERNAME"] = "dummy"
        os.environ["CONFLUENCE_USERNAME"] = "dummy"
        os.environ["CONFLUENCE_PASSWORD"] = "dummy"
        with mock_api(
            mock_get_responses=mock_gets,
            mock_put_responses=mock_puts,
            mock_post_responses=mock_posts,
        ):
            yield
    else:
        yield


def _hash_json(data: dict[str, Any]):
    return sha256(json.dumps(data).encode()).hexdigest()


def hash_str(data: str):
    data = re.sub(r"\n|\s{2,}", "", data)
    return sha256(data.encode()).hexdigest()


@pytest.mark.usefixtures("mock_requests")
def test_get_page_metadata(page_id: int, metadata_path: Path, expected_get_metadata_response: str):
    get_page_meta_data(page_id, metadata_path)
    with metadata_path.open() as file:
        result = _hash_json(json.load(file))
        assert_that(result).is_equal_to(expected_get_metadata_response)


@pytest.fixture(name="attachment_id")
def fxt_attachment_id():
    return 232111237


@pytest.fixture(name="test_image_path")
def fxt_test_image_path():
    return Path(__file__).parent.joinpath("data/dependencies.png")


@pytest.mark.usefixtures("mock_requests")
def test_update_attachment_by_id(page_id: int, attachment_id: int, test_image_path: Path):
    results = update_attachment_by_id(
        page_id=page_id, attachment_id=attachment_id, path=test_image_path
    )
    assert_that(results.status_code).is_equal_to(200)


@pytest.fixture(name="expected_attachment_data_path")
def fxt_expected_attachment_data_path():
    if os.getenv("USE_LOCAL"):
        return Path("expected_attachment_results.json")
    return Path(__file__).parent.joinpath("data/expected_attachment_results.json")


@pytest.fixture(name="expected_attachment_data")
def fxt_expected_attachment_data(
    expected_attachment_data_path: Path,
) -> dict[str, Any]:
    with expected_attachment_data_path.open() as file:
        return json.load(file)


@pytest.fixture(name="expected_dependency_title")
def fxt_expected_dependency_title() -> str:
    return "test.png"


@pytest.fixture(name="expected_dependency_attachment")
def fxt_expected_dependency_attachment(expected_dependency_title: str):
    return Attachment(id="232111237", name=expected_dependency_title, file_size=61997)


@pytest.mark.usefixtures("mock_requests")
def test_get_attachment_data(
    page_id: int,
    expected_dependency_attachment: Attachment,
    expected_dependency_title: str,
):
    results = get_attachment_data(page_id=page_id)
    assert_that(results).contains_entry(
        {expected_dependency_title: expected_dependency_attachment}
    )


@pytest.mark.usefixtures("mock_requests")
def test_token_authentication():
    confluence_connection = ConfluenceConnection()
    header = {**confluence_connection._base_headers, **confluence_connection._auth_header}
    resource = confluence_connection.contents_url.format(PAGE_ID)
    url = f"{confluence_connection._host}{resource}"
    requests_api = get_requests_api()
    response = requests_api.get(url=url, headers=header)
    assert response.status_code == 200
