"""."""
from typing import TypedDict, cast

from ska_tmc_cdm.messages.central_node.common import DishAllocation
from ska_tmc_cdm.messages.subarray_node.configure.core import (
    DishConfiguration,
    PointingConfiguration,
)

from .target_spec import ArraySpec, BaseTargetSpec, TargetSpecs
from .base import ReceptorName, MeerkatDishHame, DishName


class _ResourceConfiguration(TypedDict):
    receptors: list[str]


class Dishes(TargetSpecs):
    """_summary_."""

    _dishes_initialized = False

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
        if not self._dishes_initialized:
            TargetSpecs.__init__(self, base_target_specs, array)
            self.dish_specs: dict[str, list[ReceptorName | MeerkatDishHame]] = {
                "two": ["SKA001", "SKA002"],
                "three": ["SKA001", "SKA002", "SKA003"],
                "four": ["SKA001", "SKA002", "SKA003", "SKA004"],
                # vis-receive script doesn't allow the above resources
                # in the current visibility-receive test because it is running
                # for Low, and the above names are for Mid dishes,
                # while below we have Low station names.
                # TODO: set up the testing infrastructure to properly
                #  distinguish between Mid and Low
                #  (see tests/resources/models/obsconfig/vis_receive_config.py)
                "mkt-default": ["MKT001", "MKT002"],
            }
            self._dishes_initialized = True

    @property
    def dishes(self) -> list[DishName]:
        """_summary_.

        :return: _description_
        :rtype: list[ReceptorName | TempLow | TempLow]
        """
        dish_list: list[DishName] = []
        for target in self.target_specs.values():
            if isinstance(target.dishes, list):
                dish_list = list(set([*dish_list, *target.dishes]))
            elif dishes := self.dish_specs.get(target.dishes):
                dish_list = list(set([*dish_list, *dishes]))
        return dish_list

    @property
    def dish_allocation(self):
        """_summary_.

        :return: _description_
        :rtype: _type_
        """
        adapted_dishes = [dish for dish in self.dishes]
        return DishAllocation(adapted_dishes)

    @property
    def resource_configuration(self):
        """_summary_.

        :return: _description_
        :rtype: _type_
        """
        return _ResourceConfiguration(receptors=cast(list[str], self.dishes))

    def get_pointing_configuration(self, target_id: str | None = None):
        """_summary_.

        :param target_id: _description_, defaults to None
        :type target_id: str | None, optional
        :return: _description_
        :rtype: _type_
        """
        return PointingConfiguration(self.get_target_spec(target_id).target)

    def get_dish_configuration(self, target_id: str | None = None):
        """_summary_.

        :param target_id: _description_, defaults to None
        :type target_id: str | None, optional
        :return: _description_
        :rtype: _type_
        """
        return DishConfiguration(self.get_target_spec(target_id).band)
