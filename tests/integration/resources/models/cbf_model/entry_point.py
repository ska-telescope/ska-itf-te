"""Domain logic for the cbf."""

import json
import logging
import os
from time import sleep
from typing import List, cast

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.event_handling.builders import get_message_board_builder
from ska_ser_skallop.mvp_control.configuration import configuration as conf
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import base
from ska_ser_skallop.mvp_control.entry_points.composite import (
    CompositeEntryPoint,
    MessageBoardBuilder,
)
from ska_ser_skallop.utils.singleton import Memo

from ..base.object_with_obsconfig import HasObservation

logger = logging.getLogger(__name__)


class LogEnabled:
    """class that allows for logging if set by env var."""

    def __init__(self) -> None:
        """."""
        self._live_logging = bool(os.getenv("DEBUG_ENTRYPOINT"))
        tel = names.TEL().skamid
        assert tel
        self._tel = tel

    def _log(self, mssage: str):
        if self._live_logging:
            logger.info(mssage)


class StartUpStep(base.StartUpStep, LogEnabled):
    """Implementation of Startup step for CBF."""

    def __init__(self, nr_of_subarrays: int) -> None:
        """_summary_.

        :param nr_of_subarrays: _description_
        :type nr_of_subarrays: int
        """
        super().__init__()
        self.nr_of_subarrays = nr_of_subarrays
        self.cbf_controller = con_config.get_device_proxy(self._tel.csp.cbf.controller)

    def do_startup(self):
        """Domain logic for starting up a telescope on the interface to CBF.

        This implements the set_telescope_to_running method on the entry_point.
        """
        self.cbf_controller.command_inout("On")

    def set_wait_for_do_startup(self) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited.

        for before startup of cbf is done.
        :return: brd
        """
        brd = get_message_board_builder()

        brd.set_waiting_on(self._tel.csp.cbf.controller).for_attribute("state").to_become_equal_to(
            "ON", ignore_first=False
        )
        # subarrays
        for index in range(1, self.nr_of_subarrays + 1):
            brd.set_waiting_on(self._tel.csp.cbf.subarray(index)).for_attribute(
                "state"
            ).to_become_equal_to("ON", ignore_first=False)
        return brd

    def set_wait_for_doing_startup(self) -> MessageBoardBuilder:
        """
        Not implemented.

        :raises NotImplementedError: Raises the error
                when implementation is not done.
        """
        raise NotImplementedError()

    def set_wait_for_undo_startup(self) -> MessageBoardBuilder:
        """Domain logic for what needs to be waited for switching the sdp off.

        :return: _description_
        :rtype: MessageBoardBuilder
        """
        brd = get_message_board_builder()
        brd.set_waiting_on(self._tel.csp.cbf.controller).for_attribute("state").to_become_equal_to(
            "OFF", ignore_first=False
        )
        # subarrays
        for index in range(1, self.nr_of_subarrays + 1):
            brd.set_waiting_on(self._tel.csp.cbf.subarray(index)).for_attribute(
                "state"
            ).to_become_equal_to("OFF", ignore_first=False)
        return brd

    def undo_startup(self):
        """Domain logic for switching the cbf off."""
        self.cbf_controller.command_inout("Off")


class CbfAssignResourcesStep(base.AssignResourcesStep, LogEnabled, HasObservation):
    """Implementation of Assign Resources Step for cbf."""

    def __init__(self) -> None:
        """Init object."""
        super().__init__()
        HasObservation.__init__(self)

    def do_assign_resources(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        composition: types.Composition,  # pylint: disable=
        sb_id: str,
    ):
        """Domain logic for assigning resources to a subarray in cbf.

        This implments the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        :param composition: The assign resources configuration paramaters
        :param sb_id: a generic ide to identify a sb to assign resources
        """
        config = self.observation.dish_allocation.receptor_ids
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with AddReceptors: {config} ")
        subarray.command_inout("AddReceptors", config)

    def undo_assign_resources(self, sub_array_id: int):
        """Domain logic for releasing resources on a subarray in sdp.

        This implments the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with RemoveAllReceptors")
        subarray.command_inout("RemoveAllReceptors")

    def set_wait_for_do_assign_resources(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray assign resources is done.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "IDLE", ignore_first=False
        )

        return builder

    def set_wait_for_doing_assign_resources(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Not implemented.

        :param sub_array_id: The index id of the subarray to control
        :raises NotImplementedError: Raises the error
                when implementation is not done.
        """
        raise NotImplementedError()

    def set_wait_for_undo_resources(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited for subarray releasing resources is done.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "EMPTY", ignore_first=False
        )

        return builder


class CbfConfigureStep(base.ConfigureStep, LogEnabled, HasObservation):
    """Implementation of Configure Scan Step for CBF."""

    def __init__(self) -> None:
        """Init object."""
        super().__init__()
        self._tel = names.TEL()

    def do_configure(
        self,
        sub_array_id: int,
        configuration: types.ScanConfiguration,
        sb_id: str,
        duration: float,
    ):
        """Domain logic for configuring a scan on subarray in cbf.

        This implments the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param configuration: The assign resources configuration paramaters
        :param sb_id: a generic ide to identify a sb to assign resources
        :param duration: duration for scan
        """
        # scan duration needs to be a singleton in order to keep track of scan
        # settings between configure scan and run scan
        Memo(scan_duration=duration)
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        standard_configuration = conf.generate_standard_conf(sub_array_id, sb_id, duration)
        cbf_config = json.loads(standard_configuration)["csp"]["cbf"]
        common = json.loads(standard_configuration)["csp"]["common"]
        cbf_config["common"] = common
        cbf_standard_configuration = json.dumps({"cbf": cbf_config, "common": common})
        self._log(
            f"commanding {subarray_name} with ConfigureScan:" f" {cbf_standard_configuration} "
        )
        subarray.command_inout("ConfigureScan", cbf_standard_configuration)

    def undo_configure(self, sub_array_id: int):
        """Domain logic for clearing configuration on a subarray in cbf.

        This implments the clear_configuration method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with command GoToIdle")
        subarray.command_inout("GoToIdle")

    def set_wait_for_do_configure(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for configuring a scan is done.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to("READY")
        return builder

    def set_wait_for_doing_configure(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Not implemented.

        :param sub_array_id: The index id of the subarray to control
        :raises NotImplementedError: Raises the error when
                implementation is not done.
        """
        raise NotImplementedError()

    def set_wait_for_undo_configure(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray clear scan config is done.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to("IDLE")
        return builder


class CbfScanStep(base.ScanStep, LogEnabled):
    """Implementation of Scan Step for CBF."""

    def __init__(self) -> None:
        """Init object."""
        super().__init__()
        self._tel = names.TEL()

    def do_scan(self, sub_array_id: int):
        """Domain logic for running a scan on subarray in cbf.

        This implments the scan method on the entry_point.

        :param sub_array_id: The index id of the subarray to control

        :raises Exception: Raise exception if the scan command fails
        """
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        scan_config_arg = json.dumps({"scan_id": 1})
        scan_duration = cast(float, Memo().get("scan_duration"))
        self._log(f"Commanding {subarray_name} to Scan with {scan_config_arg}")
        try:
            subarray.command_inout("Scan", scan_config_arg)
            sleep(scan_duration)
            subarray.command_inout("EndScan")
        except Exception as exception:
            logger.exception(exception)
            raise exception

    def set_wait_for_do_scan(self, sub_array_id: int) -> MessageBoardBuilder:
        """No-op as there is no scanning command.

        :param sub_array_id: The index id of the subarray to control
        :return: message board builder
        """
        return get_message_board_builder()

    def undo_scan(self, sub_array_id: int):
        """No-op as no undo for scan is needed.

        :param sub_array_id: The index id of the subarray to control
        """

    def set_wait_for_doing_scan(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be done for waiting for subarray to be scanning.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "SCANNING"
        )
        return builder

    def set_wait_for_undo_scan(self, sub_array_id: int) -> MessageBoardBuilder:
        """No-op as no undo for scan is needed.

        :param sub_array_id: The index id of the subarray to control
        :return: None
        """
        return get_message_board_builder()


class CBFSetOnlineStep(base.SetOnlineStep, LogEnabled):
    """Domain logic for setting csp to online."""

    def __init__(self, nr_of_subarrays: int) -> None:
        """_summary_.

        :param nr_of_subarrays: _description_
        :type nr_of_subarrays: int
        """
        super().__init__()
        self.nr_of_subarrays = nr_of_subarrays

    def do_set_online(self):
        """Domain logic for setting devices in csp to online."""
        controller_name = self._tel.csp.cbf.controller
        controller = con_config.get_device_proxy(controller_name)
        self._log(f"Setting adminMode for {controller_name} to '0' (ONLINE)")
        controller.write_attribute("adminmode", 0)
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.csp.cbf.subarray(index)
            subarray = con_config.get_device_proxy(subarray_name)
            self._log(f"Setting adminMode for {subarray_name} to '0' (ONLINE)")
            subarray.write_attribute("adminmode", 0)

    def set_wait_for_do_set_online(self) -> MessageBoardBuilder:
        """Domain logic for waiting for setting to online to be complete.

        :return: builder
        """
        controller_name = self._tel.csp.cbf.controller
        builder = get_message_board_builder()
        builder.set_waiting_on(controller_name).for_attribute("adminMode").to_become_equal_to(
            "ONLINE", ignore_first=False
        )
        builder.set_waiting_on(controller_name).for_attribute("state").to_become_equal_to(
            ["OFF", "ON"], ignore_first=False
        )
        for index in range(1, self.nr_of_subarrays + 1):
            subarray = self._tel.csp.cbf.subarray(index)
            builder.set_waiting_on(subarray).for_attribute("adminMode").to_become_equal_to(
                "ONLINE", ignore_first=False
            )
            builder.set_waiting_on(subarray).for_attribute("state").to_become_equal_to(
                ["OFF", "ON"], ignore_first=False
            )
        return builder

    def undo_set_online(self):
        """Domain logic for setting devices in csp to offline."""
        controller_name = self._tel.csp.cbf.controller
        controller = con_config.get_device_proxy(controller_name)
        self._log(f"Setting adminMode for {controller_name} to '1' (OFFLINE)")
        controller.write_attribute("adminmode", 1)
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.csp.cbf.subarray(index)
            subarray = con_config.get_device_proxy(subarray_name)
            self._log(f"Setting adminMode for {subarray_name} to '1' (OFFLINE)")
            subarray.write_attribute("adminmode", 1)

    def set_wait_for_undo_set_online(self) -> MessageBoardBuilder:
        """
        Domain logic for waiting for setting to offline to be complete.

        :return: builder
        """
        controller_name = self._tel.csp.cbf.controller
        builder = get_message_board_builder()
        builder.set_waiting_on(controller_name).for_attribute("adminMode").to_become_equal_to(
            "OFFLINE", ignore_first=False
        )
        for index in range(1, self.nr_of_subarrays + 1):
            subarray = self._tel.csp.cbf.subarray(index)
            builder.set_waiting_on(subarray).for_attribute("adminMode").to_become_equal_to(
                "OFFLINE", ignore_first=False
            )
        return builder

    def set_wait_for_doing_set_online(self) -> MessageBoardBuilder:
        """
        Not implemented.

        :raises NotImplementedError: Raises the error when
                implementation is not done.
        """
        raise NotImplementedError()


class CBFEntryPoint(CompositeEntryPoint, HasObservation):
    """Derived Entrypoint scoped to CBF element."""

    nr_of_subarrays = 2

    def __init__(self) -> None:
        """_summary_."""
        super().__init__()
        self.set_online_step = CBFSetOnlineStep(self.nr_of_subarrays)
        self.start_up_step = StartUpStep(self.nr_of_subarrays)
        self.assign_resources_step = CbfAssignResourcesStep()
        self.configure_scan_step = CbfConfigureStep()
        self.scan_step = CbfScanStep()
