"""."""

from pathlib import Path
from typing import NamedTuple

from .base import AbstractFactory, BaseDiagramDependency
from .diagram_builder import DiagramBuilder
from .factory import get_config
from .implementation import Platform, get_default_factory
from .rendering import diagram_context


class DiagramsFromConfig(NamedTuple):
    """_summary_.

    :param NamedTuple: _description_
    :type NamedTuple: _type_
    """

    dependency_diagram: Path
    platform_diagram: Path

    @property
    def dependency_diagram_size(self) -> int:
        """_summary_.

        :return: _description_
        :rtype: int
        """
        return self.dependency_diagram.stat().st_size

    @property
    def platform_diagram_size(self) -> int:
        """_summary_.

        :return: _description_
        :rtype: int
        """
        return self.platform_diagram.stat().st_size


def generate_diagrams_from_config(
    source: Path,
    dest: Path | None = None,
    factory: AbstractFactory[BaseDiagramDependency] | None = None,
) -> DiagramsFromConfig:
    """Create dependencies and platform diagrams.

    :param source: path from where configs are coming from
    :type source: Path
    :param dest: path where diagrams will be temporarily stored, defaults to None
    :type dest: Path | None, optional
    :param factory: _description_, defaults to None
    :type factory: AbstractFactory[BaseDiagramDependency] | None, optional
    :return: _description_
    :rtype: DiagramsFromConfig
    """
    if factory is None:
        actual_factory = get_default_factory(source)
    else:
        actual_factory = factory
    release = get_config(source, actual_factory)  # type: ignore
    items = release.parts
    builder = DiagramBuilder(release.as_context, [*items], diagram_context)
    if dest is None:
        dest1 = "dependencies"
        dest2 = "platform"
    else:
        dest1 = dest.joinpath("dependencies.png")
        dest2 = dest.joinpath("platform.png")
    deps = [item for item in items if not isinstance(item, Platform)]
    dependency_diagram = builder.build(dest1, None, "png", *deps)
    platforms = [item for item in items if isinstance(item, Platform)]
    builder.reset()
    platform_diagram = builder.build(dest2, None, "png", *platforms)
    return DiagramsFromConfig(dependency_diagram, platform_diagram)
