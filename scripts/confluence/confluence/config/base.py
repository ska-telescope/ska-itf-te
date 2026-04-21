"""."""

import abc
from pathlib import Path
from typing import Any, Generic, TypeVar

from typing_extensions import Self


class Entity:
    """_summary_."""

    def __init__(self, name: str, version: str, root: bool = False, alias: str = "") -> None:
        """_summary_.

        :param name: _description_
        :type name: str
        :param version: _description_
        :type version: str
        :param root: _description_, defaults to False
        :type root: bool
        :param alias: _description_, defaults to ""
        :type alias: str
        """
        self._name = name
        self._version = version
        self._root = root
        self._alias = alias

    @property
    def name(self):
        """_summary_.

        :return: _description_
        :rtype: _type_
        """
        return self._name

    @property
    def version(self):
        """_summary_.

        :return: _description_
        :rtype: _type_
        """
        return self._version

    @property
    def root(self):
        """_summary_.

        :return: _description_
        :rtype: _type_
        """
        return self._root

    @property
    def alias(self):
        """_summary_.

        :return: _description_
        :rtype: _type_
        """
        return self._alias


A = TypeVar("A", bound="AbstractDependency")


class AbstractDependency(Entity):
    """."""

    def __init__(
        self,
        name: str,
        version: str = "",
        dependencies: list[A] = [],
        platformDependents: list[A] = [],
        root: Any = False,
        alias: str = "",
    ):
        """_summary_.

        :param name: _description_
        :type name: str
        :param version: _description_, defaults to ""
        :type version: str
        :param dependencies: _description_, defaults to []
        :type dependencies: list[A]
        :param platformDependents: _description_, defaults to []
        :type platformDependents: list[A]
        :param root: _description_, defaults to False
        :type root: Any
        :param alias: _description_, defaults to ""
        :type alias: str
        """
        Entity.__init__(self, name, version, root, alias)
        self.dependencies = dependencies
        self.platformDependents = platformDependents

    @property
    def name(self) -> str:
        """_summary_.

        :return: _description_
        :rtype: str
        """
        return self._name


C = TypeVar("C", bound="AbstractNode")


class AbstractNode(Entity):
    """."""

    def __init__(
        self,
        name: str,
        version: str,
        children: list[Self],
        root: bool = False,
        disable_base_init: bool = False,
        alias: str = "",
    ) -> None:
        """_summary_.

        :param name: _description_
        :type name: str
        :param version: _description_
        :type version: str
        :param children: _description_
        :type children: list[Self]
        :param root: _description_, defaults to False
        :type root: bool
        :param disable_base_init: _description_, defaults to False
        :type disable_base_init: bool
        :param alias: _description_, defaults to ""
        :type alias: str
        """
        if not disable_base_init:
            super().__init__(name, version, root, alias)
        self._children = children
        self._stub = False

    @abc.abstractmethod
    def reset(self):
        """."""

    @abc.abstractmethod
    def connect_to(self, other: Self):
        """_summary_.

        :param other: _description_
        :type other: Self
        """

    def stub(self):
        """_summary_."""
        self._stub = True

    @property
    def children(self) -> list[Self]:
        """_summary_.

        :return: _description_
        :rtype: list[Self]
        """
        if self._stub:
            return []
        return self._children


class BaseDiagramDependency(AbstractDependency, AbstractNode):
    """."""

    pass


T = TypeVar("T", bound=BaseDiagramDependency)


_global_current_path: Path | None = None


def _set__global_current_path(path: Path):
    global _global_current_path
    _global_current_path = path


def get_global_current_path() -> Path:
    """_summary_.

    :return: _description_
    :rtype: Path
    """
    global _global_current_path
    assert _global_current_path, "Ypu need to first set the current path"
    return _global_current_path


class AbstractFactory(Generic[T]):
    """."""

    def __init__(self, source: Path) -> None:
        """Initialize a factory for a dependency.

        :param source: path to where dependencies are store
        :type source: Path
        """
        _set__global_current_path(source)

    @abc.abstractmethod
    def get_dependency(
        self,
        name: str,
        version: str = "",
        dependencies: list[T] = [],
        platformDependents: list[T] = [],
        root: Any = False,
        alias: str = "",
    ) -> AbstractDependency:
        """_summary_.

        :param name: _description_
        :type name: str
        :param version: _description_, defaults to ""
        :type version: str
        :param dependencies: _description_, defaults to []
        :type dependencies: list[AbstractDependency]
        :param platformDependents: _description_, defaults to []
        :type platformDependents: list[AbstractDependency]
        :param root: _description_, defaults to False
        :type root: Any
        :param alias: _description_, defaults to ""
        :type alias: str
        """
