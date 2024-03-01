"""."""

from .env import get_observation_config


class HasObservation:
    """Inject an Observation.

    Not sure what this means
    """

    def __init__(self) -> None:
        """Init Object."""
        self.observation = get_observation_config()
