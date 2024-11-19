"""Module containing telescope teardown tools which are implemented based on ADR-8."""

import os
from dataclasses import dataclass, field

from tango import DevState
from ska_control_model import ObsState
from utils.enums import DishMode
from typing import Dict, List

# TODO: Get these  helper classes moved into utils
from tests.integration.tmc.conftest import TMC, Dish, wait_for_event


@dataclass
class TelescopeState:
    subarray: ObsState = ObsState.EMPTY
    csp: ObsState = ObsState.EMPTY
    sdp: ObsState = ObsState.EMPTY
    dishes: Dict[str, DishMode] = field(default_factory=lambda: {"SKA001": DishMode.STANDBY_LP})


class Telescope:
    """Class representing the state of the telescope under TMC control."""

    def __init__(self, dish_ids: List[str]):
        self.sut_namespace = "ci-ska-mid-itf-at-2435-improve-test-end-to-end"
        os.environ["TANGO_HOST"] = (
            f"tango-databaseds.{self.sut_namespace}.svc.miditf.internal.skao.int:10000"
        )
        self.tmc = TMC()
        base_dish_states = {dish_id: DishMode.STANDBY_LP for dish_id in dish_ids}
        self.telescope_base_state = TelescopeState(dishes=base_dish_states)

    def teardown(self, desired_tmc_state=DevState.ON):
        """Bring telescope down to base state (immediately after telescope ON) first, then to the desired state.

        :param desired_tmc_state: _description_, defaults to DevState.ON
        :type desired_tmc_state: _type_, optional
        """
        current_telescope_state = self.get_current_state()

        if current_telescope_state == self.telescope_base_state:
            return

        # Teardown the dishes
        self._teardown_dishes()

    def _teardown_dishes(self, current_dish_states: Dict[str, DishMode]):
        """Teardown dishes from current state into mode which corresponds to the telescope base state dish mode

        :param current_dish_states: _description_
        :type current_dish_states: Dict[str, DishMode]
        """
        for dish_id in current_dish_states.keys():

            if current_dish_states[dish_id] == self.telescope_base_state.dishes[dish_id]:
                continue

            dish = self.tmc.get_dish_leaf_node_dp(dish_id)

            if self.telescope_base_state.dishes[dish_id] == DishMode.STANDBY_LP:
                # Teardown from OPERATE
                if current_dish_states[dish_id] == DishMode.OPERATE:
                    dish.TrackStop()
                    dish.SetStandbyFPMode()
                    wait_for_event(dish, "dishMode", DishMode.STANDBY_FP)
                    dish.SetStandbyLPMode()
                    wait_for_event(dish, "dishMode", DishMode.STANDBY_LP)
            else:
                print(
                    f"Teardown of dish to {self.telescope_base_state.dishes[dish_id]} has not been implemented"
                )

    def get_current_state(self) -> TelescopeState:
        subarray_state = self.tmc.subarray_node.obsState
        csp_state = self.tmc.csp_subarray_leaf_node.cspSubarrayObsState
        sdp_state = self.tmc.sdp_subarray_leaf_node.sdpSubarrayObsState
        dish_states = {
            dish_id: self.tmc.get_dish_leaf_node_dp(dish_id).dishMode
            for dish_id in self.telescope_base_state.dishes.keys()
        }
        current_telescope_state = TelescopeState(subarray_state, csp_state, sdp_state, dish_states)
        return current_telescope_state
