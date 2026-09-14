# type: ignore
"""."""
import json
from pathlib import Path
from typing import Literal, cast

from schema import And, Optional, Or, Schema, Use

from .items import AndStep, Feature, Given, Match, Result, Scenario, Step, Tag, Then, When


def getStep(
    keyword: Literal["Given", "When" "Then", "And"],
    name: str,
    line: int,
    match: Match,
    result: Result,
) -> Step:
    """_summary_.

    :param keyword: _description_
    :param name: _description_
    :param line: _description_
    :param match: _description_
    :param result: _description_
    :returns: The Step instance (either Given, When, Then or And)
    """
    if keyword == "Given":
        return Given(name, line, match, result)
    if keyword == "Then":
        return Then(name, line, match, result)
    if keyword == "When":
        return When(name, line, match, result)
    if keyword == "And":
        return AndStep(name, line, match, result)


def getScenario(
    keyword: Literal["Scenario"],
    id: str,
    name: str,
    line: int,
    description: str,
    tags: list[Tag],
    type: Literal["scenario"],
    steps: list[Step],
) -> Scenario:
    """_summary_.

    :param keyword: _description_
    :param id: _description_
    :param name: _description_
    :param line: _description_
    :param description: _description_
    :param tags: _description_
    :param type: _description_
    :param steps: _description_
    :returns: the scenario instance
    """
    return Scenario(id, name, line, description, tags, steps)


_factory: Schema = Schema(
    [
        And(
            {
                "keyword": "Feature",
                "uri": str,
                "name": str,
                "id": str,
                "line": int,
                "description": str,
                "tags": [And({"name": str, "line": int}, Use(lambda x: Tag(**x)))],
                "elements": [
                    And(
                        {
                            "keyword": "Scenario",
                            "id": str,
                            "name": str,
                            "line": int,
                            "description": str,
                            "tags": [
                                And(
                                    {"name": str, "line": int},
                                    Use(lambda x: Tag(**x)),
                                )
                            ],
                            "type": "scenario",
                            "steps": [
                                And(
                                    {
                                        "keyword": Or("Given", "When", "Then", "And"),
                                        "name": str,
                                        "line": int,
                                        "match": {"location": str},
                                        "result": And(
                                            {
                                                "status": Or("passed", "failed"),
                                                "duration": int,
                                                Optional("error_message"): str,
                                            },
                                            Use(lambda x: Result(**x)),
                                        ),
                                    },
                                    Use(lambda x: getStep(**x)),
                                )
                            ],
                        },
                        Use(lambda x: getScenario(**x)),
                    )
                ],
            },
            Use(lambda x: Feature(**x)),
        )
    ]
)


def generate_schema_as_json(path: Path, name: str):
    """_summary_.

    :param path: _description_
    :type path: Path
    :param name: _description_
    :type name: str
    """
    with path.open("w") as file:
        json.dump(
            _factory.json_schema(name),
            file,
        )


def get_results(path: Path) -> list[Feature]:
    """_summary_.

    :param path: _description_
    :type path: Path
    :return: _description_
    :rtype: list[Feature]
    """
    with path.open("r") as file:
        data = json.load(file)
        return cast(list[Feature], _factory.validate(data))
