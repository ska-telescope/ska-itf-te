"""."""

import os
import subprocess
from hashlib import sha256
from pathlib import Path

import pytest
from assertpy import assert_that

from scripts.confluence.confluence.config.factory import Dependency, get_config
from scripts.confluence.confluence.config.generate_diagram import generate_diagrams_from_config
from scripts.confluence.confluence.config.implementation import Factory


@pytest.fixture(name="test_data")
def fxt_test_data() -> Path:
    """_summary_.

    :return: _description_
    :rtype: Path
    """
    return Path(__file__).parent.joinpath("data/config.yaml")


@pytest.fixture(name="expected_dependencies")
def fxt_expected_dependencies():
    """_summary_.

    :return: _description_
    :rtype: _type_
    """
    return "babef1ea90b87873208697cf6581d0eaa1e9c9583378f50b260ba70351986077"


def _digest(dependency: Dependency) -> str:
    value = (
        f"{dependency.name}{dependency.version}"
        f"{''.join(d.name+d.version for d in dependency.dependencies)}"
        f"{''.join(d.name+d.version for d in dependency.platformDependents)}"
    )
    return sha256(value.encode()).hexdigest()


def get_digest(dependencies: list[Dependency]):
    """_summary_.

    :param dependencies: _description_
    :type dependencies: list[Dependency]
    :return: _description_
    :rtype: _type_
    """
    value = "".join([_digest(d) for d in dependencies])
    return sha256(value.encode()).hexdigest()


@pytest.fixture(name="factory")
def fxt_factory(test_data: Path):
    """_summary_.

    :param test_data: _description_
    :type test_data: Path
    :return: _description_
    :rtype: _type_
    """
    return Factory(test_data)


@pytest.fixture(name="expected_dependencies_file")
def fxt_expected_dependencies_file():
    """_summary_.

    :return: _description_
    :rtype: _type_
    """
    return "8bb525e8e8a798c3f97819e04db9af4f26940f7f92d4ea1e592e9dcdfd196462"


@pytest.fixture(name="expected_platform_file")
def fxt_expected_platform_file():
    """_summary_.

    :return: _description_
    :rtype: _type_
    """
    return "c9fdea49d68215060a8420677d57369047904a89006a848f0e7dd21e1bbe9c9f"


def test_get_config(test_data: Path, expected_dependencies: str, factory: Factory):
    """_summary_.

    :param test_data: _description_
    :type test_data: Path
    :param expected_dependencies: _description_
    :type expected_dependencies: str
    :param factory: _description_
    :type factory: Factory
    """
    release = get_config(test_data, factory)  # type: ignore
    assert_that(release.as_context).is_equal_to("mid-itf:1.0.0")
    dependencies = release.parts
    assert_that(get_digest(dependencies)).is_equal_to(expected_dependencies)  # type: ignore


def get_digest_from_image(path: Path):
    """_summary_.

    :param path: _description_
    :type path: Path
    :return: _description_
    :rtype: _type_
    """
    with path.open("rb") as file:
        return sha256(file.read()).hexdigest()


def graphviz_installed() -> bool:
    """_summary_.

    :return: _description_
    :rtype: bool
    """
    with open(os.devnull, "w", encoding="utf-8") as devnull:
        retval = subprocess.call(
            ["dpkg", "-s", "graphviz"], stdout=devnull, stderr=subprocess.STDOUT
        )
    return retval == 0


def test_generate_diagrams_from_config(
    test_data: Path,
    factory: Factory,
    expected_dependencies_file: str,
    expected_platform_file: str,
):
    """_summary_.

    :param test_data: _description_
    :type test_data: Path
    :param factory: _description_
    :type factory: Factory
    :param expected_dependencies_file: _description_
    :type expected_dependencies_file: str
    :param expected_platform_file: _description_
    :type expected_platform_file: str
    """
    if not graphviz_installed():
        pytest.skip("graphviz required for test!")
    # should be '/builds/ska-telescope/ska-ser-skallop/build' in the pipeline
    path = Path(Path(__file__).parent.parent.parent.parent, "build")
    assert path.exists()
    diagrams = generate_diagrams_from_config(test_data, path, factory)  # type: ignore
    assert_that(get_digest_from_image(diagrams.dependency_diagram)).is_equal_to(
        expected_dependencies_file
    )
    assert_that(get_digest_from_image(diagrams.platform_diagram)).is_equal_to(
        expected_platform_file
    )
