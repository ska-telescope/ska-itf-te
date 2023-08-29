"""."""
from .env import get_observation_config


class HasObservation:
    """."""

    def __init__(self) -> None:
        """_summary_."""
        self.observation = get_observation_config()
