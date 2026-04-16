# type: ignore
"""."""
from typing import Any, cast

import yaml
from schema import And, Schema, Use

from .base import AbstractDependency, get_global_current_path


class Chart:
    """."""

    def __init__(self, name: str, version: str) -> None:
        """_summary_.

        :param name: _description_
        :type name: str
        :param version: _description_
        :type version: str
        """
        self.name = name
        self.version = version


def _get_chart_list(dependencies: list[Chart]) -> dict[str, str]:
    return {chart.name: chart.version for chart in dependencies}


_schema: Schema = Schema(
    And(
        {
            "dependencies": [
                And(
                    {"name": str, "version": str},
                    Use(lambda x: Chart(**x)),
                    ignore_extra_keys=True,
                )
            ]
        },
        Use(lambda x: _get_chart_list(**x)),
        ignore_extra_keys=True,
    ),
    ignore_extra_keys=True,
)


def _get_updated_version_from(name: str, ref: str):
    current_path = get_global_current_path()
    path = current_path.parent.joinpath(ref)
    with path.open("r") as file:
        data = yaml.load(file, Loader=yaml.Loader)
        results = cast(dict[str, str], _schema.validate(data))
        return results.get(name)


class Dependency(AbstractDependency):
    """."""

    _indirect_file_ref = "file://"

    _instances: dict[str, "Dependency"] = {}

    def __new__(cls, name: str, *arg: Any, **args: Any):
        """_summary_.

        :param name: _description_
        :param arg: _description_
        :param args: _description_
        :return: _description_
        """
        if instance := cls._instances.get(name):
            return instance
        instance = object().__new__(cls)
        cls._instances[name] = instance
        return instance

    @classmethod
    def clean(cls):
        """_summary_."""
        cls._instances = {}

    def __init__(
        self,
        name: str,
        version: str = "",
        dependencies: list["Dependency"] = [],
        platformDependents: list["Dependency"] = [],
        root: Any = False,
        alias: str = "",
    ):
        """_summary_.

        :param name: _description_
        :param version: _description_
        :param dependencies: _description_, defaults to []
        :param platformDependents: _description_, defaults to []
        :param root: _description_, defaults to False
        :param alias: _description_, defaults to ""
        """
        if not hasattr(self, "_skip_init"):
            self._skip_init = True
            base_name = name
        else:
            # we re-use name so that we have the same instance
            base_name = self._name
        base_root = root is not False
        if version:
            if (updated := version.replace(self._indirect_file_ref, "")) != version:
                version = _get_updated_version_from(base_name, updated)
        super().__init__(base_name, version, dependencies, platformDependents, base_root, alias)
