"""."""

import atexit
import tempfile
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path
from typing import Callable, Generator

from .base import AbstractNode


@contextmanager
def _empty_context_manager(
    path: Path,
    cluster_name: str | None = None,
    diagram_caption: str | None = None,
):
    yield


class DiagramBuilder:
    """."""

    def __init__(
        self,
        cluster_name: str,
        nodes: list[AbstractNode],
        diagram_context: (
            Callable[[Path, str | None, str | None], AbstractContextManager[None]] | None
        ),
    ) -> None:
        """_summary_.

        :param cluster_name: _description_
        :type cluster_name: str
        :param nodes: _description_
        :type nodes: list[AbstractNode]
        :param diagram_context: _description_
        :type diagram_context: Callable[[Path, str | None, str | None],
            AbstractContextManager[None]] | None
        """
        self._nodes = nodes
        self._start = False
        self._next = self._root
        self._cluster_name = cluster_name
        self._diagram_context = (
            _empty_context_manager if diagram_context is None else diagram_context
        )

    def reset(self):
        """_summary_."""
        for node in self._nodes:
            node.reset()

    def __repr__(self) -> str:
        """_summary_.

        :return: _description_
        :rtype: str
        """
        return f"({len(self._nodes)} items)"

    @property
    def _root(self) -> AbstractNode:
        if result := [item for item in self._nodes if item.root]:
            return result[0]
        raise Exception("No root in given nodes")

    def _traverse(self, node: AbstractNode) -> Generator[AbstractNode, None, None]:
        for child in node.children:
            node.connect_to(child)
            yield child
            for inner_item in self._traverse(child):
                yield inner_item

    def build(
        self,
        path: Path | None | str = None,
        diagram_caption: str | None = None,
        file_type: str = "png",
        *roots: AbstractNode,
    ) -> Path:
        """_summary_.

        :param path: _description_
        :type path: Path
        :param diagram_caption: _description_, defaults to None
        :type diagram_caption: str | None
        :param file_type: _description_
        :param roots: _roots__
        :returns: the data from the image as a filepath being read
        """
        file_manager = _FileManager(path, file_type=file_type)
        if not roots:
            roots = (self._root,)
        with self._diagram_context(file_manager.file, self._cluster_name, diagram_caption):
            for root in roots:
                for _ in self._traverse(root):
                    pass
        return file_manager.file


class _FileManager:
    def __init__(self, path: Path | None | str = None, file_type: str = "png") -> None:
        if isinstance(path, str):
            filename = path
            path = None
        else:
            filename = "drawing"
        if path is None:
            self._dir_path = Path(tempfile.mkdtemp())
            atexit.register(self._clean)
            self._registered_to_clean = True
            self.file = self._dir_path.joinpath(f"{filename}.{file_type}")
        else:
            self._dir_path = None
            self._registered_to_clean = False
            self.file = path

    def _clean(self):
        assert self._registered_to_clean
        self.file.unlink()
        assert self._dir_path
        self._dir_path.rmdir()
