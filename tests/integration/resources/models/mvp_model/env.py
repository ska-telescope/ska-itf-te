"""Creates a global env for a test and test session."""

from typing import TypedDict

from ..obsconfig.config import Observation


class ENV(TypedDict):
    """Environment for an observation.

    :param TypedDict: _description_
    """

    observation: Observation | None


env = ENV(observation=None)


def get_observation_config() -> Observation:
    """Get an observation config.

    :return:Observation: Observation config
    """
    # pylint: disable=global-variable-not-assigned
    global env
    if env["observation"] is None:
        env["observation"] = Observation()
    return env["observation"]


def init_observation_config() -> Observation:
    """Initialise an observation config.

    :return:Observation: Observation config
    """
    # pylint: disable=global-variable-not-assigned
    global env
    env["observation"] = Observation()
    return env["observation"]
