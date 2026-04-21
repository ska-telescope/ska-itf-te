"""."""

from pathlib import Path
from typing import Any, cast

from typing_extensions import Self

from .base import AbstractFactory, BaseDiagramDependency
from .dependency import Dependency
from .rendering import ConfigurationItem


class DiagramDependency(BaseDiagramDependency, Dependency, ConfigurationItem):
    """_summary_.

    :param Dependency: _description_
    :type Dependency: _type_
    :param ConfigurationItem: _description_
    :type ConfigurationItem: _type_
    """

    def __init__(
        self,
        name: str,
        version: str = "",
        dependencies: list[Self] = ...,
        platformDependents: list[Self] = ...,
        root: Any = False,
        alias: str = "",
    ):
        """_summary_.

        :param name: _description_
        :type name: str
        :param version: _description_, defaults to ""
        :type version: str
        :param dependencies: _description_, defaults to ...
        :type dependencies: list[Self]
        :param platformDependents: _description_, defaults to ...
        :type platformDependents: list[Self]
        :param root: _description_, defaults to False
        :type root: Any
        :param alias: _description_, defaults to ""
        :type alias: str
        """
        Dependency.__init__(
            self, name, version, [*dependencies], [*platformDependents], root, alias
        )
        ConfigurationItem.__init__(
            self, name, version, [*dependencies], root, disable_base_init=True, alias=alias
        )
        if platformDependents:
            self.__class__ = Platform
        # ConfigurationItem.__init__(self, name, version) is already done
        # since they both share the name and version attribute


class Platform(DiagramDependency):
    """."""

    def connect_to(self, other: Self, forward: bool = True):
        """_summary_.

        :param other: _description_
        :type other: Self
        :param forward: _description_, defaults to True
        :type forward: bool
        :return: _description_
        :rtype: _type_
        """
        return super().connect_to(other, forward=False)

    def _stub_children(self):
        for dep in self.platformDependents:
            if not isinstance(dep, Platform):
                cast(ConfigurationItem, dep).stub()

    @property
    def children(self) -> list[Any]:
        """_summary_.

        :return: _description_
        :rtype: list[Any]
        """
        self._stub_children()
        return self.platformDependents


class Factory(AbstractFactory[DiagramDependency]):
    """."""

    def get_dependency(  # type : ignore
        self,
        name: str,
        version: str = "",
        dependencies: list[DiagramDependency] = [],
        platformDependents: list[DiagramDependency] = [],
        root: Any = False,
        alias: str = "",
    ):
        """_summary_.

        :param name: _description_
        :type name: str
        :param version: _description_, defaults to ""
        :type version: str
        :param dependencies: _description_, defaults to []
        :type dependencies: list[Dependency]
        :param platformDependents: _description_, defaults to []
        :type platformDependents: list[Dependency]
        :param root: _description_, defaults to False
        :type root: Any
        :param alias: _description_, defaults to ""
        :type alias: str
        :return: _description_
        :rtype: _type_
        """
        return DiagramDependency(name, version, dependencies, platformDependents, root, alias)


def get_default_factory(source: Path):
    """_summary_.

    :param source: _description_
    :type source: Path
    :return: _description_
    :rtype: _type_
    """
    return Factory(source)
