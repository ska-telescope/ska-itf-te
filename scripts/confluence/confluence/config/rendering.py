"""."""

import re
from contextlib import contextmanager
from pathlib import Path

from diagrams import Cluster, Diagram, Edge, Node
from typing_extensions import Self

from .base import AbstractNode


class ConfigurationItem(AbstractNode):
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
        super().__init__(name, version, children, root, disable_base_init, alias)
        self._node: None | Node = None
        self.edges: list[Edge] = []
        self.edgeSet: dict[str, bool] = {}

    def reset(self):
        """_summary_."""
        self._node: None | Node = None
        self.edges: list[Edge] = []

    def __repr__(self) -> str:
        """_summary_.

        :return: _description_
        :rtype: str
        """
        return f"Node item {self.name}"

    @property
    def root(self):
        """_summary_.

        :return: _description_
        :rtype: _type_
        """
        return self._root

    @property
    def node(self):
        """_summary_.

        :return: _description_
        :rtype: _type_
        """
        if self._node is None:
            if self.alias:
                name = self.alias
            else:
                name = self.name
            name = name.replace("ska-", "")
            name += f"\n{self.version}\n"
            name += "\n".join(["" for _ in range(4)])
            self._node = Node(name)
        return self._node

    def connect_to(self, other: Self, forward: bool = True):
        """_summary_.

        :param other: _description_
        :type other: Self
        :param forward: _description_, defaults to True
        :type forward: bool
        """
        # Do not connect to a node that we already have a connection to.
        if other.name in self.edgeSet:
            return
        self.edgeSet[other.name] = True
        edge = Edge(self.node, forward)
        self.node.connect(other.node, edge)
        self.edges.append(edge)


@contextmanager
def diagram_context(
    path: Path,
    cluster_name: str | None = None,
    diagram_caption: str | None = None,
):
    """_summary_.

    :param path: _description_
    :type path: Path
    :param diagram_caption: _description_, defaults to None
    :type diagram_caption: str | None
    :param cluster_name: _description_
    :yields: _description_
    """
    diagram_name = path.name.removesuffix(path.suffix)
    filename = path.as_posix()
    filename = re.sub(r"(\.\w+)", "", filename)
    if cluster_name is None:
        cluster_name = diagram_name
    caption = diagram_caption if diagram_caption is not None else diagram_name
    node_attr = {"fixedsize": "false"}
    with Diagram(caption, filename=filename, show=False, direction="TB", node_attr=node_attr):
        with Cluster(cluster_name):
            yield
