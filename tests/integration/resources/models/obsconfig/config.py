"""."""
from dishes import Dishes
from tests.integration.resources.models.obsconfig.target_spec import ArraySpec, BaseTargetSpec


class Observation(Dishes):
    """_summary_."""

    def __init__(
        self,
        base_target_specs: dict[str, BaseTargetSpec] | None = None,
        array: ArraySpec | None = None,
    ) -> None:
        """_summary_.

        :param base_target_specs: _description_, defaults to None
        :type base_target_specs: dict[str, BaseTargetSpec] | None, optional
        :param array: _description_, defaults to None
        :type array: ArraySpec | None, optional
        """
        Dishes.__init__(self, base_target_specs, array)
