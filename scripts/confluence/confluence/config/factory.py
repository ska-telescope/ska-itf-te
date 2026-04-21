# type: ignore
"""."""
from pathlib import Path
from typing import Any, cast

import yaml
from schema import And, Optional, Or, Schema, Use

from .base import AbstractDependency, AbstractFactory, BaseDiagramDependency
from .dependency import Dependency


def _get_dependencies(dependencies: dict[str, dict[str, Any]]):
    _dependency_list: list[AbstractDependency] = []
    for name, args in dependencies.items():
        _dependency_list.append(_get_dependency(name, **args))
    return _dependency_list


_dependency_factory: AbstractFactory | None = None


def _set_dependency_factory(dependency_factory: AbstractFactory):
    global _dependency_factory
    _dependency_factory = dependency_factory


def _get_dependency(
    name: str,
    version: str = "",
    dependencies: list[AbstractDependency] = [],
    platformDependents: list[AbstractDependency] = [],
    root: Any = False,
    alias: Any = None,
):
    global _dependency_factory
    assert _dependency_factory, "You need to set a dependency factory first"
    return _dependency_factory.get_dependency(
        name, version, dependencies, platformDependents, root, alias
    )


class Release:
    """."""

    def __init__(self, name: str, version: str, parts: list[BaseDiagramDependency]) -> None:
        """_summary_.

        :param name: _description_
        :type name: str
        :param version: _description_
        :type version: str
        :param parts: _description_
        :type parts: list[BaseDiagramDependency]
        """
        self.name = name
        self.version = version
        self.parts = parts

    @property
    def as_context(self) -> str:
        """_summary_.

        :return: _description_
        :rtype: str
        """
        return f"{self.name}:{self.version}"


_factory: Schema = Schema(
    And(
        {
            "name": str,
            "version": str,
            "parts": And(
                {
                    str: {
                        "version": str,
                        Optional("dependencies"): [And(str, Use(lambda x: _get_dependency(x)))],
                        Optional("platformDependents"): [
                            And(str, Use(lambda x: _get_dependency(x)))
                        ],
                        Optional("root"): Or(None, str),
                        Optional("alias"): Or(None, str),
                    },
                },
                Use(_get_dependencies),
            ),
        },
        Use(lambda x: Release(**x)),
    )
)


def get_schema():
    """_summary_.

    :return: _description_
    :rtype: _type_
    """
    return _factory


def _assert_there_exist_one_root(dependencies: list[AbstractDependency]):
    if result := [item for item in dependencies if item.root]:
        if len(result) > 1:
            raise AssertionError(
                "There can only be one root in the"
                " configuration data but you gave: "
                f"{[r.name for r in result]} as roots"
            )
    else:
        raise AssertionError("No root found in the given list of dependencies")


def _assert_dependency_properly_defined(
    dependencies: list[AbstractDependency],
):
    if result := [item for item in dependencies if not item.version]:
        if len(result) > 1:
            raise AssertionError(
                "The following dependencies have not been properly defined,"
                " please defined them as entities in the root:"
                f"{[r.name for r in result]}"
            )
        raise AssertionError(
            f"The dependency {result[0].name} have not been properly defined,"
            " please defined them as entities in the root:"
        )


def get_config(path: Path, factory: AbstractFactory[BaseDiagramDependency]) -> Release:
    """_summary_.

    :param path: _description_
    :type path: Path
    :param factory: _description_
    :type factory: AbstractFactory
    :return: _description_
    :rtype: Release
    """
    _set_dependency_factory(factory)
    with path.open("r") as file:
        data = yaml.load(file, Loader=yaml.Loader)
        release = cast(Release, _factory.validate(data))
        dependencies = cast(list[Dependency], release.parts)
        _assert_there_exist_one_root(dependencies)
        _assert_dependency_properly_defined(dependencies)
        return release
