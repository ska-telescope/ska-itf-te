"""Module containing telescope teardown tools which are implemented based on ADR-8."""

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List

from ska_control_model import ObsState
from ska_control_model._dev_state import DevState

# TODO: Get these  helper classes moved into utils
from tests.integration.tmc.conftest import TMC, EventWaitTimeout, wait_for_event
from utils.enums import DishMode

# TODO: Think about passing an instance of logger, and not global logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


@dataclass
class TelescopeState:
    """Class representing the telescope state.

    :return: _description_
    :rtype: _type_
    """

    telescope: DevState = DevState.OFF
    subarray: ObsState = ObsState.EMPTY
    csp: ObsState = ObsState.EMPTY
    sdp: ObsState = ObsState.EMPTY
    dishes: Dict[str, DishMode] = field(default_factory=lambda: {"SKA001": DishMode.STANDBY_LP})

    def __str__(self):
        """Generate string representation of telescope state.

        :return: _description_
        :rtype: _type_
        """
        dishes_str = ", ".join(f"{dish}: {mode.name}" for dish, mode in self.dishes.items())
        return (
            f"\nTelescope State:\n"
            f"  Telescope: {self.telescope.name}\n"
            f"  Subarray: {self.subarray.name}\n"
            f"  CSP: {self.csp.name}\n"
            f"  SDP: {self.sdp.name}\n"
            f"  Dishes: {dishes_str}"
        )


class TelescopeHandler:
    """Class containing methods to manipulate the state ofthe telescope under TMC control."""

    def __init__(self, sut_namespace: str, dish_ids: List[str]):
        """_summary_.

        :param sut_namespace: _description_
        :type sut_namespace: str
        :param dish_ids: _description_
        :type dish_ids: List[str]
        """
        self.sut_namespace = sut_namespace
        os.environ["TANGO_HOST"] = (
            f"tango-databaseds.{self.sut_namespace}.svc.miditf.internal.skao.int:10000"
        )
        self.tmc = TMC()
        base_dish_states = {dish_id: DishMode.STANDBY_LP for dish_id in dish_ids}
        self.telescope_base_state = TelescopeState(dishes=base_dish_states)

    def teardown(self, desired_state: TelescopeState = None):
        """Bring telescope down to desired TMC state - base state by default.

        :param desired_state: _description_, defaults to None
        :type desired_state: TelescopeState
        """
        if desired_state is None:
            desired_state = self.telescope_base_state

        current_telescope_state = self.get_current_state()
        if current_telescope_state == desired_state:
            logger.info(f"Telescope is already at the base state: {self.telescope_base_state}")
            return

        # Teardown the dishes
        self._teardown_dishes(current_dish_states=current_telescope_state.dishes)

        current_telescope_state = self.get_current_state()
        if current_telescope_state == desired_state:
            return
        # Teardown System Under Test (SUT) first via TMC subarray
        try:
            self._teardown_sut_subsystem(
                subsystem="tmc_subarray", current_state=current_telescope_state.subarray
            )
        except EventWaitTimeout:
            logger.info(
                "Failed to teardown telescope via the TMC Subarray. Attempting contingencies"
            )

            # Re-evaluate telescope state and continue teardown if necessary
            current_telescope_state = self.get_current_state()
            if current_telescope_state == desired_state:
                return

            # Teardown SUT from transitionary states and via leafnodes
            self._tear_down_transitionary(
                self.tmc.subarray_node,
                current_state=self.get_current_state().subarray,
                obs_state_name="obsState",
            )

            # Re-evaluate telescope state
            current_telescope_state = self.get_current_state()
            if current_telescope_state == desired_state:
                return

            if current_telescope_state.csp != self.telescope_base_state.csp:
                self._teardown_sut_subsystem(
                    subsystem="csp", current_state=current_telescope_state.csp
                )

            # Re-evaluate telescope state
            current_telescope_state = self.get_current_state()
            if current_telescope_state == desired_state:
                return

            if current_telescope_state.sdp != self.telescope_base_state.sdp:
                current_telescope_state = self.get_current_state()
                self._teardown_sut_subsystem(
                    subsystem="sdp", current_state=current_telescope_state.sdp
                )

        # Re-evaluate telescope state
        current_telescope_state = self.get_current_state()
        if current_telescope_state == desired_state:
            return

        # Turn OFF the telescope
        # self._turn_off_telescope()

        # Re-evaluate telescope state
        current_telescope_state = self.get_current_state()
        if current_telescope_state != desired_state:
            logger.error("Failed to teardown the telescope to the base state")

    def _teardown_dishes(self, current_dish_states: Dict[str, DishMode]):
        """Teardown dishes from current state down to the base state.

        :param current_dish_states: _description_
        :type current_dish_states: Dict[str, DishMode]
        """
        for dish_id in current_dish_states.keys():
            if current_dish_states[dish_id] == self.telescope_base_state.dishes[dish_id]:
                logger.info(
                    f"Dish {dish_id} is already at the following base state: "
                    f"{self.telescope_base_state.dishes[dish_id]}"
                )
                continue

            logger.info(
                f"Tearing down dish {dish_id} from {current_dish_states[dish_id]}"
                f" to {self.telescope_base_state.dishes[dish_id]}"
            )
            dish = self.tmc.get_dish_leaf_node_dp(dish_id)

            if self.telescope_base_state.dishes[dish_id] == DishMode.STANDBY_LP:
                # Teardown from OPERATE
                if current_dish_states[dish_id] == DishMode.OPERATE:
                    dish.AbortCommands()
                    dish.SetStandbyFPMode()
                    wait_for_event(dish, "dishMode", DishMode.STANDBY_FP, timeout=30)
                    dish.SetStandbyLPMode()
                    wait_for_event(dish, "dishMode", DishMode.STANDBY_LP, timeout=30)

                # Teardown from STANDBY_FP
                if current_dish_states[dish_id] == DishMode.STANDBY_FP:
                    dish.SetStandbyLPMode()
                    wait_for_event(dish, "dishMode", DishMode.STANDBY_LP, timeout=30)

                # Teardown from UNKNOWN
                if current_dish_states[dish_id] == DishMode.UNKNOWN:
                    dish.SetStowMode()
                    wait_for_event(dish, "dishMode", DishMode.STOW, timeout=30)
                    dish.SetStandbyLPMode()
                    wait_for_event(dish, "dishMode", DishMode.STANDBY_LP, timeout=30)
            else:
                logger.error(
                    f"Teardown of dish to {self.telescope_base_state.dishes[dish_id]}"
                    " has not been implemented"
                )

    def _teardown_sut_subsystem(self, subsystem: str, current_state: ObsState):
        """Teardown the System Under Test (SUT) subsystems via TMC.

        TeardownTMC Subarray, Central Signal Processor (CSP) and SDP (Science Data Processor).
        Subsystems are torn down to the base state.

        :param subsystem: _description_
        :type subsystem: str
        :param current_state: _description_
        :type current_state: ObsState
        """
        if subsystem == "sdp":
            proxy = self.tmc.sdp_subarray_leaf_node
            obs_state_name = "sdpSubarrayObsState"
            subsystem_base_state = self.telescope_base_state.sdp
        if subsystem == "csp":
            proxy = self.tmc.csp_subarray_leaf_node
            obs_state_name = "cspSubarrayObsState"
            subsystem_base_state = self.telescope_base_state.csp
        if subsystem == "tmc_subarray":
            proxy = self.tmc.subarray_node
            obs_state_name = "ObsState"
            subsystem_base_state = self.telescope_base_state.subarray

        if current_state == subsystem_base_state:
            logger.info(
                f"{subsystem} is already at the following base state: {subsystem_base_state}"
            )
            return

        if subsystem_base_state == ObsState.EMPTY:
            logger.info(f"Tearing down {subsystem} from {current_state} to {subsystem_base_state}")
            # Teardown from SCANNING
            if current_state == ObsState.SCANNING:
                proxy.EndScan()
                wait_for_event(proxy, obs_state_name, ObsState.READY, timeout=30)
                proxy.End()
                wait_for_event(proxy, obs_state_name, ObsState.IDLE, timeout=30)
                proxy.ReleaseAllResources()
                wait_for_event(proxy, obs_state_name, ObsState.EMPTY, timeout=30)

            # Teardown from READY
            if current_state == ObsState.READY:
                proxy.End()
                wait_for_event(proxy, obs_state_name, ObsState.IDLE, timeout=30)
                proxy.ReleaseAllResources()
                wait_for_event(proxy, obs_state_name, ObsState.EMPTY, timeout=30)

            # Teardown from IDLE
            if current_state == ObsState.IDLE:
                proxy.ReleaseAllResources()
                wait_for_event(proxy, obs_state_name, ObsState.EMPTY, timeout=30)

            # Teardown from ABORTED
            if current_state == ObsState.ABORTED:
                proxy.Restart()
                wait_for_event(proxy, obs_state_name, ObsState.EMPTY, timeout=30)

            # # Teardown from a transitionary state
            self._tear_down_transitionary(
                proxy,
                current_state,
                obs_state_name,
            )

            # Teardown from FAULT
            if current_state == ObsState.FAULT:
                print(f"{subsystem} teardown from {ObsState.FAULT} note implemented")

        else:
            print(f"Teardown of CSP to {self.telescope_base_state.csp} has not been implemented")

    def _tear_down_transitionary(self, proxy, current_state, obs_state_name):
        """Teardown the subsystem from a transitionary state down to the base state.

        :param proxy: _description_
        :type proxy: _type_
        :param current_state: _description_
        :type current_state: _type_
        :param obs_state_name: _description_
        :type obs_state_name: _type_
        """
        # Teardown from a transitionary state (*ING)
        if re.findall(r"\w+ING\b", current_state.name):
            proxy.Abort()
            wait_for_event(proxy, obs_state_name, ObsState.ABORTED, timeout=30)
            proxy.Restart()
            wait_for_event(proxy, obs_state_name, ObsState.EMPTY, timeout=30)

    def _turn_off_telescope(self):
        """Turn OFF the telescope."""
        proxy = self.tmc.central_node

        proxy.TelescopeOff()
        try:
            wait_for_event(proxy, "telescopeState", DevState.OFF, timeout=30)
        except EventWaitTimeout as e:
            if proxy.telescopeState == DevState.UNKNOWN:
                logger.info("Could not transition telescope from UNKNOWN to OFF")
            else:
                raise e

    def get_current_state(self) -> TelescopeState:
        """Return the current telescope state.

        :return: _description_
        :rtype: TelescopeState
        """
        telescope_state = DevState(self.tmc.central_node.telescopeState)
        subarray_state = self.tmc.subarray_node.obsState
        csp_state = self.tmc.csp_subarray_leaf_node.cspSubarrayObsState
        sdp_state = self.tmc.sdp_subarray_leaf_node.sdpSubarrayObsState
        dish_states = {
            dish_id: self.tmc.get_dish_leaf_node_dp(dish_id).dishMode
            for dish_id in self.telescope_base_state.dishes.keys()
        }
        current_telescope_state = TelescopeState(
            telescope_state, subarray_state, csp_state, sdp_state, dish_states
        )
        return current_telescope_state
