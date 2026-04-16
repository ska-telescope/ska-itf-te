"""."""

import abc
import base64
import json
import os
import re
from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Union, cast

import requests
from lxml import etree
from mock import Mock
from requests import Response
from typing_extensions import Self

_mock_requests: bool = False
_mock_responses: dict[str, Any] = {}


@lru_cache
def get_jira(jira_id: str) -> list[dict[str, Any]]:
    """_summary_.

    :param jira_id: _description_
    :type jira_id: str
    :return: _description_
    :rtype: bool
    """
    connection = get_connection()
    results = connection.get_test(jira_id)
    return results


@lru_cache
def get_jira_detail(jira_id: int) -> dict[str, Any]:
    """_summary_.

    :param jira_id: _description_
    :type jira_id: int
    :return: _description_
    :rtype: dict[str, Any]
    """
    connection = get_connection()
    results = connection.get_jira(str(jira_id))
    return results


@contextmanager
def mock_requests(mock_responses: dict[str, Any]):
    """_summary_.

    :param mock_responses: _description_
    :yield: _summary_
    """
    global _mock_requests
    global _mock_responses
    _mock_requests = True
    _mock_responses = mock_responses
    yield
    _mock_requests = False
    _mock_responses = []


def _mock_get(url: str, headers: dict[str, str] = {}):
    global _mock_responses
    response = Mock(Response)
    if url.find("rest/api/2/issue") > 0:
        key = re.findall(r"(?<=rest\/api\/2\/issue\/)(\d+)", url)[0]
        if result := _mock_responses.get(key):
            response.content = json.dumps(result)
            return response
    else:
        key = re.findall(r"(?<=keys=)(.+)", url)[0]
        if result := _mock_responses.get(key):
            response.content = json.dumps([result])
            return response
    response.content = json.dumps([])
    return response


def get_requests():
    """_summary_.

    :return: _description_
    """
    if _mock_requests:
        mock_requests = Mock(requests)
        cast(Mock, mock_requests.get).side_effect = _mock_get
        return mock_requests
    return requests


class Connection:
    """_summary_."""

    xray_get_tests = "/rest/raven/1.0/api/test?keys={}"
    xray_get_jira = "/rest/api/2/issue/{}"

    def __init__(self) -> None:
        """_summary_."""
        hostname = os.getenv("JIRA_HOST", "jira.skatelescope.org")
        host = f"https://{hostname}"
        if not (token := os.getenv("JIRA_AUTH")):
            username = os.getenv("JIRA_USERNAME")
            if username is None:
                username = os.getenv("CONFLUENCE_USERNAME")
            password = os.getenv("JIRA_PASSWORD")
            if password is None:
                password = os.getenv("CONFLUENCE_PASSWORD")
            assert (
                username and password
            ), "expected a username and password since no JIRA_AUTH has been set"
            token = base64.b64encode(f"{username}:{password}".encode("ascii")).decode("ascii")
        self._base_headers = {"Authorization": f"Basic {token}"}
        self.host = host

    @property
    def _requests(self):
        return cast(requests, get_requests())

    def get_test(self, issue_id: str) -> list[dict[str, Any]]:
        """_summary_.

        :param issue_id: _description_
        :return: _description_
        """
        headers = self._base_headers.copy()
        headers["Accept"] = "application/json"
        url = f"{self.host}{self.xray_get_tests.format(issue_id)}"
        response = self._requests.get(
            url,
            headers=headers,
        )
        return json.loads(response.content)

    def get_jira(self, issue_id: str) -> dict[str, Any]:
        """_summary_.

        :param issue_id: _description_
        :return: _description_
        """
        headers = self._base_headers.copy()
        headers["Accept"] = "application/json"
        url = f"{self.host}{self.xray_get_jira.format(issue_id)}"
        response = self._requests.get(
            url,
            headers=headers,
        )
        return json.loads(response.content)


def get_connection():
    """_summary_.

    :return: _description_
    :rtype: _type_
    """
    return Connection()


class _AbstractElementWrapper:
    ns: dict[str, str] = {"ac": "ac:"}

    @property
    @abc.abstractmethod
    def head(self) -> Any:
        """."""

    @property
    @abc.abstractmethod
    def tail(self) -> Any:
        """."""

    def connect(
        self,
        other: Union["_AbstractElementWrapper", list["_AbstractElementWrapper"]],
    ) -> Any:
        if isinstance(other, list):
            for item in other:
                self.head.append(item.tail)
            return self
        self.head.append(other.tail)
        return other

    def __gt__(self, other: Self):
        self.connect(other)

    def __str__(self) -> str:
        result = cast(str, etree.tostring(self.tail, encoding="unicode"))  # type: ignore
        return result.replace(' xmlns:ac="ac:"', "")


class _JiraParameter(_AbstractElementWrapper):
    def __init__(self, text: str, name: str) -> None:
        self._element = etree.Element(
            "{%s}parameter" % self.ns["ac"],
            {"{%s}name" % self.ns["ac"]: name},
            self.ns,
        )
        self._element.text = text

    @property
    def head(self):
        return self._element

    @property
    def tail(self):
        return self._element


class _JiraServerParameter(_JiraParameter):
    def __init__(self, text: str = "") -> None:
        super().__init__(text, "server")


class _JiraColumnIdsParameter(_JiraParameter):
    def __init__(self, text: str = "") -> None:
        super().__init__(text, "columnIds")


class _JiraColumnsParameter(_JiraParameter):
    def __init__(self, text: str = "") -> None:
        super().__init__(text, "columns")


class _JiraServerIDParameter(_JiraParameter):
    def __init__(self, text: str = "") -> None:
        super().__init__(text, "serverId")


class _JiraKeyParameter(_JiraParameter):
    def __init__(self, text: str = "") -> None:
        super().__init__(text, "key")


class _JiraWrapper(_AbstractElementWrapper):
    def __init__(self) -> None:
        self._root = etree.Element("div", {"class": "content-wrapper"}, {})
        self._branch = etree.SubElement(self._root, "p", {}, {})
        self._branch.text = ""
        self._head = etree.SubElement(
            self._branch,
            "{%s}structured-macro" % self.ns["ac"],
            {
                "{%s}name" % self.ns["ac"]: "jira",
                "{%s}schema-version" % self.ns["ac"]: "1",
                "{%s}macro-id" % self.ns["ac"]: "0d3d7ccb-1fad-4452-a507-043e075f3b58",
            },
            self.ns,
        )

    @property
    def head(self):
        return self._head

    @property
    def tail(self):
        return self._root


def generate_jira_wrapper(jira_key: str) -> str:
    """_summary_.

    :param jira_key: _description_
    :type jira_key: str
    :return: _description_
    :rtype: str
    """
    (element := _JiraWrapper()).connect(
        [
            _JiraServerParameter("SKA Jira"),
            _JiraColumnIdsParameter(
                "issuekey,summary,issuetype,"
                "created,updated,duedate,assignee,"
                "reporter,priority,status,resolution"
            ),
            _JiraColumnsParameter(
                "key,summary,type,created,"
                "updated,due,assignee,reporter,"
                "priority,status,resolution"
            ),
            _JiraServerIDParameter("ad75ab71-1245-3349-8713-12bcc32bca7c"),
            _JiraKeyParameter(jira_key),
        ]
    )
    return str(element)
