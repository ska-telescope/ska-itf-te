"""Update Confluence html and attachment contents."""

import json
import os
import re
from contextlib import contextmanager
from json import dump, loads
from pathlib import Path
from typing import Any, NamedTuple, TypedDict, cast

import requests
from mock import Mock
from requests import Response
from requests.auth import HTTPBasicAuth

RESOURCE = {
    "fetch_page": "content/",
    "update": "content/",
    "fetch_attachment": "content/",
    "fetch_attachment_by_id": "content",
}


_request_api = None
_mock_get_responses: dict[str, Any] = {}
_mock_post_responses: dict[str, Any] = {}
_mock_put_responses: dict[str, Any] = {}


def get_requests_api():
    """Get confluence requests.

    :return: returns an instance of request module
    :rtype: request module.
    """
    global _request_api
    if _request_api is None:
        _request_api = requests
    return _request_api


def _mock_raise_for_status():
    raise Exception()


def _response_with(data: dict[str, Any] | None):
    response = Mock(requests.Response)
    if data is not None:
        text = json.dumps(data)
        response.content = text.encode()
        response.text = text
        response.status_code = 200
        cast(Mock, response.json).return_value = data
    else:
        cast(Response, response).raise_for_status = _mock_raise_for_status
    return response


def _mock_get(url: str, *args: Any, **kwargs: Any):
    response_key = _response_key(url, **kwargs)
    data = _mock_get_responses.get(response_key)
    return _response_with(data)


def _mock_post(url: str, *args: Any, **kwargs: Any):
    page_id = _response_key(url, **kwargs)
    data = _mock_post_responses.get(page_id)
    return _response_with(data)


def _mock_put(url: str, *args: Any, **kwargs: Any):
    page_id = _response_key(url, **kwargs)
    data = _mock_put_responses.get(page_id)
    return _response_with(data)


def _response_key(url: str, **kwargs: Any) -> str:
    if result := re.findall(r"(?<=/rest\/api\/content\/)(\w+)(?=\/|$)", url):
        key = result[0]
        if url.find("/child/attachment/") > 0:
            key += "child_attachment"
        elif "params" in kwargs:
            key += "".join([f"{key}_{value}" for key, value in kwargs["params"].items()])
        return key
    return ""


@contextmanager
def mock_api(
    mock_get_responses: dict[str, Any] = {},
    mock_post_responses: dict[str, Any] = {},
    mock_put_responses: dict[str, Any] = {},
):
    """Responses mock APi used as a context manager.

    :param mock_get_responses: dictionary of mock get data, defaults to {}
    :type mock_get_responses: dict[str, Any], optional
    :param mock_post_responses: dictionary of mock post data, defaults to {}
    :type mock_post_responses: dict[str, Any], optional
    :param mock_put_responses: dictionary of mock put data, defaults to {}
    :type mock_put_responses: dict[str, Any], optional
    :yield: mock api responses
    """
    global _request_api
    global _mock_get_responses
    global _mock_post_responses
    global _mock_put_responses
    mock_requests = Mock(requests)
    cast(Mock, mock_requests.get).side_effect = _mock_get
    cast(Mock, mock_requests.post).side_effect = _mock_post
    cast(Mock, mock_requests.put).side_effect = _mock_put
    original_request_api = _request_api
    _request_api = mock_requests
    if mock_get_responses:
        _mock_get_responses = {**_mock_get_responses, **mock_get_responses}
    if mock_post_responses:
        _mock_post_responses = {**_mock_post_responses, **mock_post_responses}
    if mock_put_responses:
        _mock_put_responses = {**_mock_put_responses, **mock_put_responses}
    yield
    _request_api = original_request_api


class ConfluenceConnection:
    """Confluence connection class instantiating every request."""

    contents_url = "/rest/api/content/{}"
    attachments_url = "/rest/api/content/{}/child/attachment/"
    attachment_url = "/rest/api/content/{}/child/attachment/{}/data"

    def __init__(self) -> None:
        """Initialize confluence connection instance. Prioritizes token auth."""
        CONFLUENCE_HOST = os.getenv("CONFLUENCE_HOST")
        CONFLUENCE_SERVICE_ACCOUNT_USERNAME = os.getenv("CONFLUENCE_SERVICE_ACCOUNT_USERNAME")
        CONFLUENCE_SERVICE_ACCOUNT_TOKEN = os.getenv("CONFLUENCE_SERVICE_ACCOUNT_TOKEN")
        CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")
        CONFLUENCE_PASSWORD = os.getenv("CONFLUENCE_PASSWORD")

        token_auth = CONFLUENCE_SERVICE_ACCOUNT_USERNAME and CONFLUENCE_SERVICE_ACCOUNT_TOKEN
        basic_auth = CONFLUENCE_USERNAME and CONFLUENCE_PASSWORD
        assert CONFLUENCE_HOST, "CONFLUENCE_HOST not set"
        assert token_auth or basic_auth, "Neither token nor username and password provided"

        self._base_headers = {"Accept": "application/json"}
        self._auth_header = {"Authorization": f"Bearer {CONFLUENCE_SERVICE_ACCOUNT_TOKEN}"}
        self._host = f"https://{CONFLUENCE_HOST}"

        if token_auth:
            self._base_headers = {**self._base_headers, **self._auth_header}
            self._auth = None
        elif basic_auth:
            self._auth = HTTPBasicAuth(CONFLUENCE_USERNAME, CONFLUENCE_PASSWORD)

    def get(self, name: str, **params: Any) -> Response:
        """Perform a get api request.

        :param name: api resource name to use
        :type name: str
        :param params: extra parameters to use as part of the url
        :return: get response of confluence api
        :rtype: Response
        """
        resource = self.contents_url.format(name)
        url = f"{self._host}{resource}"
        headers = self._base_headers
        auth = self._auth
        requests_api = get_requests_api()
        return requests_api.get(url=url, auth=auth, headers=headers, params=params)

    def get_attachment_data(self, page_id: str) -> Response:
        """Get all page attachments data.

        :param page_id: confluence existing page_id
        :type page_id: str
        :return: list of page attachment data
        :rtype: Response
        """
        resource = self.attachments_url.format(page_id)
        url = f"{self._host}{resource}"
        headers = self._base_headers
        auth = self._auth
        requests_api = get_requests_api()
        return requests_api.get(url=url, auth=auth, headers=headers)

    def post_attachment(
        self,
        page_id: str,
        attachment_id: str,
        file_path: Path,
    ) -> Response:
        """Post request to update an attachment on a confluence page.

        :param page_id: confluence existing page_id
        :type page_id: str
        :param attachment_id: confluence page existing attachment_id
        :type attachment_id: str
        :param file_path: path where the image is stored
        :type file_path: Path
        :return: response object regarding the status of the uploaded image
        :rtype: Response
        """
        resource = self.attachment_url.format(page_id, attachment_id)
        url = f"{self._host}{resource}"
        headers = {**self._base_headers, **{"X-Atlassian-Token": "nocheck"}}
        auth = self._auth
        requests_api = get_requests_api()
        with file_path.open("+rb") as file:
            response = requests_api.post(url=url, auth=auth, headers=headers, files={"file": file})
        return response

    def post(
        self,
        name: str,
        data: dict[str, Any] | str | None = None,
        **params: Any,
    ) -> Response:
        """Post request to update page files.

        :param name: resource to use to make a request
        :type name: str
        :param params: params to add as part of the payload
        :param data: data(images) to be added to a confluence page
        :type data: dict[str, Any]
        :return: response object regarding adding content to confluence page
        :rtype: Response
        """
        resource = self.contents_url.format(name)
        url = f"{self._host}{resource}"
        headers = self._base_headers
        auth = self._auth
        if isinstance(data, dict):
            headers = {**headers, **{"Content-type": "application/json"}}
        else:
            file_dict = None
        requests_api = get_requests_api()
        if isinstance(data, dict):
            response = requests_api.post(
                url=url,
                auth=auth,
                headers=headers,
                json=data,
                params=params,
                files=file_dict,
            )
        else:
            response = requests_api.post(
                url=url,
                auth=auth,
                headers=headers,
                data=data,
                params=params,
                files=file_dict,
            )
        return response

    def put(
        self,
        name: str,
        data: dict[str, Any] | str,
        **params: Any,
    ) -> Response:
        """Request to update page html content.

        :param name: resource to use to make a request
        :type name: str
        :param data: html data to be updated on the confluence page
        :type data: dict[str, Any] | str
        :param params: params to use as part of the request url
        :return: response object regarding updating content on a confluence page
        :rtype: Response
        """
        resource = self.contents_url.format(name)
        url = f"{self._host}{resource}"
        headers = self._base_headers
        if isinstance(data, dict):
            headers = {**headers, **{"Content-type": "application/json"}}
        auth = self._auth
        requests_api = get_requests_api()
        if isinstance(data, dict):
            response = requests_api.put(
                url=url, auth=auth, headers=headers, json=data, params=params
            )
        else:
            response = requests_api.put(
                url=url, auth=auth, headers=headers, data=data, params=params
            )
        return response


def update_attachment_by_id(page_id: int | str, attachment_id: int | str, path: Path):
    """Update attachment by ID.

    :param page_id: confluence existing page_id
    :type page_id: int
    :param attachment_id: confluence existing attachment_id
    :type attachment_id: int
    :param path: path to where the attachment is stored
    :type path: Path
    :return: response object regarding uploading attachment by id
    :rtype: Response
    """
    connection = ConfluenceConnection()
    response = connection.post_attachment(str(page_id), str(attachment_id), file_path=path)
    response.raise_for_status()
    return response


class Attachment(TypedDict):
    """Confluence page attachment object."""

    id: str
    name: str
    file_size: int


def get_attachment_data(page_id: int | str):
    """Fetch the page attachment by id.

    :param page_id: confluence existing page_id
    :type page_id: int
    :returns: Confluence page attachments data.
    """
    connection = ConfluenceConnection()
    response = connection.get_attachment_data(str(page_id))
    response.raise_for_status()
    data = response.json()
    with open("results.json", "w", encoding="utf-8") as file:
        json.dump(data, file)
    return {
        item["title"]: Attachment(
            id=item["id"],
            name=item["title"],
            file_size=item["extensions"]["fileSize"],
        )
        for item in data["results"]
    }


def get_page_attachments(page_id: int, title: str) -> None | Attachment:
    """Fetch the page attachments.

    :param page_id: confluence existing page_id
    :param title: Title of an attachment.
    :return: Title of an attachment.
    """
    attachment_data = get_attachment_data(page_id)
    return attachment_data.get(title)


def get_page_html_content(page_id: int | str, path: Path | None = None) -> str:
    """Fetch the html content of a confluence page given the id, store the results in a temp file.

    :param page_id: confluence existing page_id
    :param path: path to where the temp confluence content is stored
    :type page_id: int
    :return: Confluence page content as html string object.
    """
    connection = ConfluenceConnection()
    response = connection.get(str(page_id), expand="body.storage")
    response.raise_for_status()

    if isinstance(response.json(), str):
        data = response.json()

    if isinstance(response.json(), dict):
        data = response.json()["body"]["storage"]["value"]
    if path is not None:
        with path.open("w") as file:
            file.write(data)
    return data


def _get_page_metadata(page_id: int | str):
    """Get confluence page information.

    :param page_id: confluence existing page_id
    :type page_id: int
    :return: response object regarding confluence page metadata
    :rtype: _type_
    """
    connection = ConfluenceConnection()
    response = connection.get(str(page_id))
    response.raise_for_status()
    return loads(response.text)


def get_page_meta_data(page_id: int, path: Path):
    """Retrieve page metadata given confluence page ID.

    :param page_id: confluence existing page id.
    :param path: Path to confluence page meta data.
    :type page_id: int
    """
    response = _get_page_metadata(page_id)

    with path.open("w") as file:
        dump(response, file)


def update_page_content(page_id: int | str, path: Path | str = Path("temp.xhtml")):
    """Update confluence page html content.

    :param page_id: confluence existing page_id
    :type page_id: int
    :param path: path to where the temp file will be stored, defaults to Path("temp.xhtml")
    :type path: Path | str, optional
    :return: response object regarding updating confluence html content
    :rtype: Response
    """
    version_number, page_title, space_key = _get_page_essentials(page_id)
    if isinstance(path, Path):
        with path.open("r", encoding="utf-8") as file:
            contents = file.read()
    else:
        contents = path
    payload = {
        "space": {"key": f"{space_key}"},
        "type": "page",
        "title": f"{page_title}",
        "version": {"number": version_number + 1},
        "body": {"storage": {"value": f"{contents}", "representation": "storage"}},
    }

    connection = ConfluenceConnection()
    response = connection.put(str(page_id), data=payload, expand="body.storage")
    response.raise_for_status()
    return response


class PageEssentials(NamedTuple):
    """Confluence page essentials object."""

    version_nr: int
    page_tile: str
    space: str


def _get_page_essentials(page_id: int | str):
    """Get confluence page current version for an update.

    :param page_id: confluence existing page id
    :type page_id: int
    :return: PageEssentials
    """
    data = _get_page_metadata(page_id)
    return PageEssentials(data["version"]["number"], data["title"], data["space"]["key"])
