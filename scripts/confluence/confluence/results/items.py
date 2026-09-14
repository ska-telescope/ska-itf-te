"""."""

from functools import reduce
from typing import Any, Literal, TypeVar, cast

from .file_helper import find_in_test_file
from .jira_helper import generate_jira_wrapper, get_jira, get_jira_detail


class Tag:
    """_summary_."""

    def __init__(self, name: str, line: int) -> None:
        """_summary_.

        :param name: _description_
        :type name: str
        :param line: _description_
        :type line: int
        """
        self.name = name
        self.line = line


class Match:
    """."""

    def __init__(self, location: str) -> None:
        """_summary_.

        :param location: _description_
        :type location: str
        """
        self.location = location


Outcome = Literal["passed", "failed"]


class Result:
    """_summary_."""

    def __init__(
        self,
        status: Outcome,
        duration: int,
        error_message: str | None = None,
    ) -> None:
        """_summary_.

        :param status: _description_
        :param duration: _description_
        :param error_message: _description_, defaults to None
        """
        self.status = status
        self.duration = duration
        self.error_message = error_message

    @property
    def failed(self) -> bool:
        """_summary_.

        :return: _description_
        """
        return self.status == "failed"

    @property
    def passed(self) -> bool:
        """_summary_.

        :return: _description_
        """
        return self.status == "passed"


class Step:
    """."""

    def __init__(
        self,
        name: str,
        line: int,
        match: Match,
        result: Result,
    ) -> None:
        """_summary_.

        :param name: _description_
        :param line: _description_
        :param match: _description_
        :param result: _description_
        """
        self.name = name
        self.line = line
        self.match = match
        self.result = result

    @property
    def failed(self) -> bool:
        """_summary_.

        :return: _description_
        :rtype: bool
        """
        return self.result.failed

    @property
    def passed(self) -> bool:
        """_summary_.

        :return: _description_
        :rtype: bool
        """
        return self.result.passed


class When(Step):
    """_summary_."""


class Then(Step):
    """_summary_."""


class Given(Step):
    """_summary_."""


class AndStep(Step):
    """_summary_."""


class Scenario:
    """_summary_."""

    def __init__(
        self,
        id: str,
        name: str,
        line: int,
        description: str,
        tags: list[Tag],
        steps: list[Step],
    ) -> None:
        """_summary_.

        :param id: _description_
        :param name: _description_
        :param line: _description_
        :param description: _description_
        :param tags: _description_
        :param steps: _description_
        """
        self.id_ = id
        self.name = name
        self.line = line
        self.description = description
        self._tags = tags
        self.steps = steps

    @property
    def path(self):
        """_summary_.

        :return: _description_
        :rtype: _type_
        """
        return find_in_test_file(self.id_)

    @property
    def result(self) -> Outcome:
        """_summary_.

        :return: _description_
        """
        if self.failed:
            return "failed"
        return "passed"

    @property
    def failed(self) -> bool:
        """_summary_.

        :return: _description_
        """
        return any(step.failed for step in self.steps)

    @property
    def passed(self) -> bool:
        """_summary_.

        :return: _description_
        """
        return not self.failed

    @property
    def tags(self) -> list[str]:
        """_summary_.

        :return: _description_
        :rtype: list[str]
        """
        return [tag.name for tag in self._tags]


class XRayTest(Scenario):
    """_summary_.

    :param Scenario: _description_
    :type Scenario: _type_
    """

    def __init__(
        self,
        id: str,
        name: str,
        line: int,
        description: str,
        tags: list[Tag],
        steps: list[Step],
    ) -> None:
        """_summary_.

        :param id: _description_
        :type id: str
        :param name: _description_
        :type name: str
        :param line: _description_
        :type line: int
        :param description: _description_
        :type description: str
        :param tags: _description_
        :type tags: list[Tag]
        :param steps: _description_
        :type steps: list[Step]
        """
        super().__init__(id, name, line, description, tags, steps)
        self._xray_id = None

    def set_xray_id(self, xray_id: str) -> None:
        """.

        :param xray_id: _description_
        :type xray_id: str
        """
        self._xray_id = xray_id

    @property
    def xray_id(self) -> str:
        """_summary_.

        :return: _description_
        :rtype: str
        """
        if self._xray_id:
            return generate_jira_wrapper(self._xray_id)
        return ""

    @staticmethod
    def _is_test_link(link: dict[str, Any]):
        return link["type"]["name"] == "Tests"

    @staticmethod
    def _is_requirement(issue: dict[str, Any] | None):
        if issue:
            return issue["fields"]["issuetype"]["name"] == "Requirement"
        return False

    @staticmethod
    def _get_jama_requirement_id(issue: dict[str, Any]) -> str | None:
        if field := issue["fields"].get("customfield_12133"):
            return field
        return None

    @staticmethod
    def _get_jama_requirement_id_with_link(issue: dict[str, Any]) -> str | None:
        if field := issue["fields"].get("customfield_12133"):
            if link := issue["fields"].get("customfield_13903"):
                return f'<a href="{link}">{field}</a>'
            return field
        return None

    def _get_requirements(self) -> list[dict[str, Any]]:
        """_summary_.

        :return: _description_
        :rtype: list[str]
        """
        issue = get_jira(self._xray_id)
        if issue:
            issue = issue[0]
            issue_detail = get_jira_detail(issue["id"])
            if issuelinks := issue_detail["fields"].get("issuelinks"):
                outwardIssues = [
                    link.get("outwardIssue") for link in issuelinks if self._is_test_link(link)
                ]
                outwardRequirements = [
                    issue["id"] for issue in outwardIssues if self._is_requirement(issue)
                ]
                return [get_jira_detail(issue) for issue in outwardRequirements]
        return []

    @property
    def requirements(self) -> list[str]:
        """_summary_.

        :return: _description_
        :rtype: list[str]
        """
        requirements_issues = self._get_requirements()
        jama_requirements = [self._get_jama_requirement_id(issue) for issue in requirements_issues]
        return [requirement for requirement in jama_requirements if requirement]

    @property
    def requirements_with_link(self) -> list[str]:
        """_summary_.

        :return: _description_
        :rtype: list[str]
        """
        requirements_issues = self._get_requirements()
        jama_requirements = [
            self._get_jama_requirement_id_with_link(issue) for issue in requirements_issues
        ]
        return [requirement for requirement in jama_requirements if requirement]


class Feature:
    """_summary_."""

    def __init__(
        self,
        keyword: Literal["Feature"],
        uri: str,
        name: str,
        id: str,
        line: int,
        description: str,
        tags: list[Tag],
        elements: list[Scenario],
    ) -> None:
        """_summary_.

        :param keyword: _description_
        :param uri: _description_
        :param name: _description_
        :param id: _description_
        :param line: _description_
        :param description: _description_
        :param tags: _description_
        :param elements: _description_
        """
        self.uri = uri
        self.name = name
        self._id = id
        self.line = line
        self.description = description
        self.tags = tags
        self.elements = elements
        self._tests: list[XRayTest] = []
        for test in self.elements:
            for tag in test.tags:
                if is_tag_unique(tag):
                    test.__class__ = XRayTest
                    test = cast(XRayTest, test)
                    test.set_xray_id(tag)
                    self._tests.append(test)

    @property
    def tests(self) -> list[XRayTest]:
        """_summary_.

        :return: _description_
        """
        return self._tests


T = TypeVar("T")


def agg(current: list[T], new: list[T]) -> list[T]:
    """_summary_.

    :param current: _description_
    :type current: list[T]
    :param new: _description_
    :type new: list[T]
    :return: _description_
    :rtype: list[T]
    """
    return [*current, *new]


def get_scoped_tags(scope: Feature, current: XRayTest) -> set[str]:
    """_summary_.

    :param scope: _description_
    :param current: _description_
    :return: _description_
    """
    mapping = [test.tags for test in scope.elements if test != current]
    if mapping:
        tags = reduce(agg, mapping)
        return set(cast(list[str], (tags)))
    return set()


def is_tag_unique(tag: str) -> bool:
    """_summary_.

    :param tag: _description_
    :return: _description_
    """
    results = get_jira(tag)
    return len(results) > 0
