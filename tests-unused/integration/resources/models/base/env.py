"""Creates a global env for a test and test session."""

from typing import TypedDict

from ..obsconfig.config import Observation


class _ENV(TypedDict):
    """."""

    observation: Observation | None


_env = _ENV(observation=None)


def get_observation_config() -> Observation:
    """_summary_.

    :return: _description_
    :rtype: Observation
    """
    # pylint: disable=global-variable-not-assigned
    global _env
    if _env["observation"] is None:
        _env["observation"] = Observation()
    return _env["observation"]


def init_observation_config() -> Observation:
    """_summary_.

    :return: _description_
    :rtype: Observation
    """
    # pylint: disable=global-variable-not-assigned
    global _env
    _env["observation"] = Observation()
    return _env["observation"]
