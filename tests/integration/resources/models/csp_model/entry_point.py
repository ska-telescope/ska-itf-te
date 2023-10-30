"""Domain logic for the csp."""
import json
import logging
import os
from time import sleep
from typing import List

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.event_handling.builders import MessageBoardBuilder, get_message_board_builder
from ska_ser_skallop.event_handling.handlers import WaitForLRCComplete
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import base
from ska_ser_skallop.mvp_control.entry_points.composite import CompositeEntryPoint
from ska_ser_skallop.utils.singleton import Memo

from ...utils.validation import CommandException, command_success
from ..mvp_model.object_with_obsconfig import HasObservation
from ..mvp_model.states import ObsState

logger = logging.getLogger(__name__)

# scan duration needs to be a singleton in order to keep track of scan
# settings between configure scan and run scan
SCAN_DURATION = 4


class LogEnabled:
    """Allow for logging if set by env var."""

    def __init__(self) -> None:
        """Set up the class."""
        self._live_logging = bool(os.getenv("DEBUG_ENTRYPOINT"))
        self._tel = names.TEL()

    def _log(self, mssage: str):
        if self._live_logging:
            logger.info(mssage)


class WithCommandID:
    """Do something with the command ID."""

    def __init__(self) -> None:
        """Set up the class."""
        self._long_running_command_subscriber = None

    @property
    def long_running_command_subscriber(self) -> WaitForLRCComplete | None:
        """_summary_.

        Returns:
        :return:WaitForLRCComplete | None: Property that awaits the longrunning command
        """
        return Memo().get("long_running_command_subscriber")

    @long_running_command_subscriber.setter
    def long_running_command_subscriber(self, subscriber: WaitForLRCComplete):
        Memo(long_running_command_subscriber=subscriber)


class StartUpStep(base.StartUpStep, LogEnabled, WithCommandID):
    """Implementation of Startup step for CSP."""

    def __init__(self, nr_of_subarrays: int) -> None:
        """Set up the class.

        :param nr_of_subarrays: _description_
        """
        super().__init__()
        self.nr_of_subarrays = nr_of_subarrays
        self.csp_controller = con_config.get_device_proxy(self._tel.csp.controller)

    def do_startup(self):
        """Domain logic for starting up a telescope on the interface to csp.

        This implements the set_telescope_to_running method on the entry_point.
        :raises CommandException: when the command returned as failed
        """
        assert self.long_running_command_subscriber
        command_id = self.csp_controller.command_inout("On", [])
        if command_success(command_id):
            self.long_running_command_subscriber.set_command_id(command_id)
        else:
            self.long_running_command_subscriber.unsubscribe_all()
            raise CommandException(command_id)

    def set_wait_for_do_startup(self) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited for before startup of csp is done.

        Returns the message board
        :return: brd
        """
        brd = get_message_board_builder()
        brd.set_waiting_on(self._tel.csp.controller).for_attribute("state").to_become_equal_to(
            "ON", ignore_first=False
        )
        self.long_running_command_subscriber = brd.set_wait_for_long_running_command_on(
            self._tel.csp.controller
        )
        # we wait for cbf vccs to be in proper initialised state
        # brd.set_waiting_on(self._tel.csp.cbf.controller).for_attribute(
        #     "reportVccState"
        # ).to_become_equal_to(["[0, 0, 0, 0]", "[0 0 0 0]"], ignore_first=False)
        for index in range(1, self.nr_of_subarrays + 1):
            brd.set_waiting_on(self._tel.csp.subarray(index)).for_attribute(
                "state"
            ).to_become_equal_to("ON", ignore_first=False)
        return brd

    def set_wait_for_doing_startup(self) -> MessageBoardBuilder:
        """
        Not implemented.

        :raises NotImplementedError: Raises the error when
                implementation is not done.
        """
        raise NotImplementedError()

    def set_wait_for_undo_startup(self) -> MessageBoardBuilder:
        """
        Domain logic for what needs to be waited for switching the csp off.

        :return: brd
        """
        brd = get_message_board_builder()
        # controller
        # the low telescope does not switch off so there is no wait
        if self._tel.skamid:
            csp_controller = str(self._tel.csp.controller)
            brd.set_waiting_on(csp_controller).for_attribute("state").to_become_equal_to(
                "OFF", ignore_first=False
            )
            # subarrays
            for index in range(1, self.nr_of_subarrays + 1):
                brd.set_waiting_on(self._tel.csp.subarray(index)).for_attribute(
                    "state"
                ).to_become_equal_to("OFF", ignore_first=False)
            self.long_running_command_subscriber = brd.set_wait_for_long_running_command_on(
                self._tel.csp.controller
            )
        return brd

    def undo_startup(self):
        """Domain logic for switching the csp off.

        :raises CommandException: when the command returned as failed
        """
        # Low CBF Controller and subarrays devices are always ON
        if self._tel.skamid:
            assert self.long_running_command_subscriber
            command_id = self.csp_controller.command_inout("Off", [])
            if command_success(command_id):
                self.long_running_command_subscriber.set_command_id(command_id)
            else:
                self.long_running_command_subscriber.unsubscribe_all()
                raise CommandException(command_id)


class CspAssignResourcesStep(base.AssignResourcesStep, LogEnabled, WithCommandID, HasObservation):
    """Implementation of Assign Resources Step for CSP."""

    def __init__(self) -> None:
        """Init object."""
        super().__init__()
        HasObservation.__init__(self)
        self._tel = names.TEL()

    def do_assign_resources(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        composition: types.Composition,  # pylint: disable=
        sb_id: str,
    ):
        """Domain logic for assigning resources to a subarray in csp.

        This implments the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        :param composition: The assign resources configuration paramaters
        :param sb_id: a generic ide to identify a sb to assign resources
        :raises CommandException: when the command returned as failed
        """
        assert self.long_running_command_subscriber
        subarray_name = self._tel.skamid.csp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        config = self.observation.generate_csp_assign_resources_config(sub_array_id).as_json
        self._log(f"commanding {subarray_name} with AssignResources: {config} ")
        subarray.set_timeout_millis(6000)
        command_id = subarray.command_inout("AssignResources", config)
        if command_success(command_id):
            self.long_running_command_subscriber.set_command_id(command_id)
        else:
            self.long_running_command_subscriber.unsubscribe_all()
            raise CommandException(command_id)

    def undo_assign_resources(self, sub_array_id: int):
        """Domain logic for releasing resources on a subarray in csp.

        This implments the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :raises CommandException: when the command returned as failed
        """
        assert self.long_running_command_subscriber
        subarray_name = self._tel.csp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with ReleaseAllResources")
        subarray.set_timeout_millis(6000)
        command_id = subarray.command_inout("ReleaseAllResources")
        if command_success(command_id):
            self.long_running_command_subscriber.set_command_id(command_id)
        else:
            self.long_running_command_subscriber.unsubscribe_all()
            raise CommandException(command_id)

    def set_wait_for_do_assign_resources(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited for subarray assign resources is done.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        self._tel = names.TEL()
        subarray_name = self._tel.csp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to("IDLE")
        self.long_running_command_subscriber = builder.set_wait_for_long_running_command_on(
            subarray_name
        )
        return builder

    def set_wait_for_doing_assign_resources(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Not implemented.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
        """
        brd = get_message_board_builder()
        subarray_name = self._tel.csp.subarray(sub_array_id)
        brd.set_waiting_on(self._tel.csp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("RESOURCING")
        self.long_running_command_subscriber = brd.set_wait_for_long_running_command_on(
            subarray_name
        )
        return brd

    def set_wait_for_undo_resources(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited for subarray releasing resources is done.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to("EMPTY")
        self.long_running_command_subscriber = builder.set_wait_for_long_running_command_on(
            subarray_name
        )
        return builder


class CspConfigureStep(base.ConfigureStep, LogEnabled, WithCommandID, HasObservation):
    """Implementation of Configure Scan Step for CSP."""

    def __init__(self) -> None:
        """Init object."""
        super().__init__()
        HasObservation.__init__(self)
        self._tel = names.TEL()

    def do_configure(
        self,
        sub_array_id: int,
        configuration: types.ScanConfiguration,
        sb_id: str,
        duration: float,
    ):
        """Domain logic for configuring a scan on subarray in csp.

        This implments the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param configuration: The assign resources configuration paramaters
        :param sb_id: a generic ide to identify a sb to assign resources
        :param duration: duration of scan
        :raises CommandException: when the command returned as failed
        """
        # scan duration needs to be a memorised for
        # future objects that mnay require it
        assert self.long_running_command_subscriber
        Memo(scan_duration=duration)
        subarray_name = self._tel.skamid.csp.subarray(sub_array_id)
        cbf_configuration = self.observation.generate_csp_scan_config().as_json
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with Configure:" f" {cbf_configuration} ")
        command_id = subarray.command_inout("Configure", cbf_configuration)
        if command_success(command_id):
            self.long_running_command_subscriber.set_command_id(command_id)
        else:
            self.long_running_command_subscriber.unsubscribe_all()
            raise CommandException(command_id)

    def undo_configure(self, sub_array_id: int):
        """
        Domain logic for clearing configuration on a subarray in csp.

        This implments the clear_configuration method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :raises CommandException: when the command returned as failed
        """
        assert self.long_running_command_subscriber
        subarray_name = self._tel.csp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with command GoToIdle")
        command_id = subarray.command_inout("GoToIdle")
        if command_success(command_id):
            self.long_running_command_subscriber.set_command_id(command_id)
        else:
            self.long_running_command_subscriber.unsubscribe_all()
            raise CommandException(command_id)

    def set_wait_for_do_configure(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited for configuring a scan is done.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to("READY")
        self.long_running_command_subscriber = builder.set_wait_for_long_running_command_on(
            subarray_name
        )
        return builder

    def set_wait_for_doing_configure(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Specify what needs to be waited for a subarray to be in a state of configuring.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "CONFIGURING"
        )
        self.long_running_command_subscriber = builder.set_wait_for_long_running_command_on(
            subarray_name
        )
        return builder

    def set_wait_for_undo_configure(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited for subarray clear scan config is done.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to("IDLE")
        self.long_running_command_subscriber = builder.set_wait_for_long_running_command_on(
            subarray_name
        )
        return builder


class CspScanStep(base.ScanStep, LogEnabled, WithCommandID, HasObservation):
    """Implement a Scan Step for CSP."""

    def __init__(self) -> None:
        """Init object."""
        super().__init__()
        HasObservation.__init__(self)
        self._tel = names.TEL()

    def do_scan(self, sub_array_id: int):
        """Domain logic for running a scan on subarray in csp.

        This implments the scan method on the entry_point.

        :param sub_array_id: The index id of the subarray to control

        :raises Exception: Raise exception in do method of scan command
        :raises CommandException: when the command returned as failed
        """
        assert self.long_running_command_subscriber
        scan_config_arg = json.dumps(self.observation.generate_csp_run_scan_config())
        scan_duration = Memo().get("scan_duration")
        self._tel = names.TEL()
        subarray_name = self._tel.csp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(
            f"Commanding {subarray_name} to Scan with {scan_config_arg}"
            f" with scan_duration {scan_duration}"
        )
        try:
            command_id = subarray.command_inout("Scan", scan_config_arg)
            if command_success(command_id):
                self.long_running_command_subscriber.set_command_id(command_id)
                sleep(scan_duration)
                current_state = subarray.read_attribute("obsState")
                if current_state.value == ObsState.SCANNING:
                    subarray.command_inout("EndScan")
            else:
                raise CommandException(command_id)
        except Exception as exception:
            logger.exception(exception)
            raise exception

    def set_wait_for_do_scan(self, sub_array_id: int) -> MessageBoardBuilder:
        """Build a no-op as there is no scanning command.

        :param sub_array_id: The index id of the subarray to control
        :return: message board builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.subarray(sub_array_id)
        self.long_running_command_subscriber = builder.set_wait_for_long_running_command_on(
            subarray_name
        )
        return builder

    def undo_scan(self, sub_array_id: int):
        """Build a no-op as there is no scanning command.

        :param sub_array_id: The index id of the subarray to control
        """

    def set_wait_for_doing_scan(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Domain logic specifyig what needs to be done for waiting for subarray to be scanning.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "SCANNING", ignore_first=False
        )
        self.long_running_command_subscriber = builder.set_wait_for_long_running_command_on(
            subarray_name
        )
        return builder

    def set_wait_for_undo_scan(self, sub_array_id: int) -> MessageBoardBuilder:
        """Wait without reason - this is a no-op as no undo for scan is needed.

        :param sub_array_id: The index id of the subarray to control
        :return: message board builder
        """
        return get_message_board_builder()


class CSPSetOnlineStep(base.SetOnlineStep, LogEnabled):
    """Domain logic for setting CSP to online."""

    def __init__(self, nr_of_subarrays: int) -> None:
        """Set up the class.

        :param nr_of_subarrays: Number of subarrays
        """
        super().__init__()
        self.nr_of_subarrays = nr_of_subarrays

    def do_set_online(self):
        """Domain logic for setting devices in CSP to online."""
        controller_name = self._tel.csp.controller
        controller = con_config.get_device_proxy(controller_name)
        admin_mode = controller.read_attribute("adminmode").value
        if admin_mode != 0:
            self._log(f"Setting adminMode for {controller_name} to '0' (ONLINE)")
            controller.write_attribute("adminmode", 0)
            # The commented out section below is not necessary, as promised by Gianluca, 2023/10/26
            # for index in range(1, self.nr_of_subarrays + 1):
            #     subarray_name = self._tel.csp.subarray(index)
            #     subarray = con_config.get_device_proxy(subarray_name)
            #     self._log(f"Setting adminMode for {subarray_name} to '0' (ONLINE)")
            #     subarray.write_attribute("adminmode", 0)

        simulation_mode = controller.read_attribute("cbfSimulationMode").value
        if simulation_mode != 0:
            self._log(
                f"Setting simulation_mode for {controller_name} to '0' (Real Hardware Controlled)"
            )
            controller.write_attribute("cbfSimulationMode", 0)

    def set_wait_for_do_set_online(self) -> MessageBoardBuilder:
        """
        Domain logic for waiting for setting to online to be complete.

        :return: builder
        """
        controller_name = self._tel.csp.controller
        builder = get_message_board_builder()
        builder.set_waiting_on(controller_name).for_attribute("adminMode").to_become_equal_to(
            "ONLINE", ignore_first=False
        )
        builder.set_waiting_on(controller_name).for_attribute("state").to_become_equal_to(
            ["OFF", "ON"], ignore_first=False
        )
        for index in range(1, self.nr_of_subarrays + 1):
            subarray = self._tel.csp.subarray(index)
            builder.set_waiting_on(subarray).for_attribute("adminMode").to_become_equal_to(
                "ONLINE", ignore_first=False
            )
            builder.set_waiting_on(subarray).for_attribute("state").to_become_equal_to(
                ["OFF", "ON"], ignore_first=False
            )
        return builder

    def undo_set_online(self):
        """Domain logic for setting devices in csp to offline."""
        controller_name = self._tel.csp.controller
        controller = con_config.get_device_proxy(controller_name)
        self._log(f"Setting adminMode for {controller_name} to '1' (OFFLINE)")
        controller.write_attribute("adminmode", 1)
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.csp.subarray(index)
            subarray = con_config.get_device_proxy(subarray_name)
            self._log(f"Setting adminMode for {subarray_name} to '1' (OFFLINE)")
            subarray.write_attribute("adminmode", 1)

    def set_wait_for_undo_set_online(self) -> MessageBoardBuilder:
        """
        Domain logic for waiting for setting to offline to be complete.

        :return: builder
        """
        controller_name = self._tel.csp.controller
        builder = get_message_board_builder()
        builder.set_waiting_on(controller_name).for_attribute("adminMode").to_become_equal_to(
            "OFFLINE", ignore_first=False
        )
        for index in range(1, self.nr_of_subarrays + 1):
            subarray = self._tel.csp.subarray(index)
            builder.set_waiting_on(subarray).for_attribute("adminMode").to_become_equal_to(
                "OFFLINE", ignore_first=False
            )
        return builder

    def set_wait_for_doing_set_online(self) -> MessageBoardBuilder:
        """
        Not implemented.

        :raises NotImplementedError: Raises the error when implementation is not done.
        """
        raise NotImplementedError()


class CSPAbortStep(base.AbortStep, LogEnabled, WithCommandID):
    """Implementation of Abort Step for CSP."""

    def do_abort(self, sub_array_id: int):
        """Domain logic for running a abort on subarray in csp.

        This implments the scan method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :raises CommandException: when the command returned as failed
        """
        assert self.long_running_command_subscriber
        subarray_name = self._tel.csp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with Abort command")
        command_id = subarray.command_inout("Abort")
        if command_success(command_id):
            self.long_running_command_subscriber.set_command_id(command_id)
        else:
            raise CommandException(command_id)

    def set_wait_for_do_abort(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for abort is done.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "ABORTED", ignore_first=False
        )
        self.long_running_command_subscriber = builder.set_wait_for_long_running_command_on(
            subarray_name
        )
        return builder


class CSPObsResetStep(base.ObsResetStep, LogEnabled):
    """Implementation of ObsReset Step for CSP."""

    def set_wait_for_do_obsreset(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Domain logic for running a obsreset on subarray in csp.

        This implments the scan method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "IDLE", ignore_first=True
        )
        self.long_running_command_subscriber = builder.set_wait_for_long_running_command_on(
            subarray_name
        )
        return builder

    def do_obsreset(self, sub_array_id: int):
        """
        Domain logic specifying what needs to be waited for obsreset is done.

        :param sub_array_id: The index id of the subarray to control
        :raises CommandException: when the command returned as failed
        """
        assert self.long_running_command_subscriber
        subarray_name = self._tel.csp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with ObsReset command")
        command_id = subarray.command_inout("Obsreset")
        if command_success(command_id):
            self.long_running_command_subscriber.set_command_id(command_id)
        else:
            raise CommandException(command_id)

    def undo_obsreset(self, sub_array_id: int):
        """
        Domain logic for releasing resources on a subarray in csp.

        This implments the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :raises CommandException: when the command returned as failed
        """
        assert self.long_running_command_subscriber
        subarray_name = self._tel.csp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with ReleaseAllResources")
        subarray.set_timeout_millis(6000)
        command_id = subarray.command_inout("ReleaseAllResources")
        if command_success(command_id):
            self.long_running_command_subscriber.set_command_id(command_id)
        else:
            raise CommandException(command_id)

    def set_wait_for_undo_obsreset(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited for subarray releasing resources is done.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to("EMPTY")
        self.long_running_command_subscriber = builder.set_wait_for_long_running_command_on(
            subarray_name
        )
        return builder


class CSPRestart(base.RestartStep, LogEnabled):
    """Restart the CSP.

    :param base: base step
    :param LogEnabled: class descriptor
    """

    def do_restart(self, sub_array_id: int):
        """Do the restart.

        :param sub_array_id: _description_
        """
        subarray_name = self._tel.csp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with Restart command")
        subarray.command_inout("Restart")

    def set_wait_for_do_restart(self, sub_array_id: int) -> MessageBoardBuilder:
        """Wait for the restart.

        :param sub_array_id: Subarray ID.

        :return:MessageBoardBuilder: Return a message board builder object
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "EMPTY", ignore_first=True
        )
        return builder


class CSPWaitReadyStep(base.WaitReadyStep, LogEnabled):
    """Wait for the SUT to be ready.

    :param base: _description_
    :param LogEnabled: _description_
    """

    def __init__(self, nr_of_subarrays: int) -> None:
        """Init object.

        :param nr_of_subarrays: _description_
        """
        super().__init__()
        self._nr_of_subarrays = nr_of_subarrays

    def set_wait_for_sut_ready_for_session(self) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited for before startup of csp is done.

        Returns the message board
        :return: builder
        :rtype: MessageBoardBuilder
        """
        builder = get_message_board_builder()
        csp_controller = self._tel.csp.controller
        builder.set_waiting_on(csp_controller).for_attribute("state").to_become_equal_to(
            ["OFF", "ON", "DISABLE"], ignore_first=False
        )
        for sub_id in range(1, self._nr_of_subarrays + 1):
            subarray = self._tel.csp.subarray(sub_id)
            builder.set_waiting_on(subarray).for_attribute("state").to_become_equal_to(
                ["OFF", "ON", "DISABLE"], ignore_first=False
            )
        return builder


class CSPEntryPoint(CompositeEntryPoint, HasObservation):
    """Derived Entrypoint scoped to CSP element."""

    nr_of_subarrays = 2

    def __init__(self) -> None:
        """Init Object."""
        super().__init__()
        HasObservation.__init__(self)
        self.set_online_step = CSPSetOnlineStep(self.nr_of_subarrays)
        self.start_up_step = StartUpStep(self.nr_of_subarrays)
        self.assign_resources_step = CspAssignResourcesStep()
        self.configure_scan_step = CspConfigureStep()
        self.scan_step = CspScanStep()
        self.abort_step = CSPAbortStep()
        self.obsreset_step = CSPObsResetStep()
        self.restart_step = CSPRestart()
        self.wait_ready = CSPWaitReadyStep(self.nr_of_subarrays)


csp_mid_assign_resources_template = {
    "interface": "https://schema.skao.int/ska-csp-assignresources/2.2",
    "subarray_id": 1,
    "dish": {"receptor_ids": ["MKT001", "MKT002"]},
}

csp_mid_configure_scan_template = {
    "interface": "https://schema.skao.int/ska-csp-configure/2.0",
    "subarray": {"subarray_name": "science period 23"},
    "common": {
        "config_id": "sbi-mvp01-20200325-00001-science_A",
        "frequency_band": "1",
        "subarray_id": 1,
    },
    "cbf": {
        "delay_model_subscription_point": "ska_mid/tm_leaf_node/csp_subarray_01/delayModel",
        "fsp": [
            {
                "fsp_id": 1,
                "function_mode": "CORR",
                "frequency_slice_id": 1,
                "integration_factor": 1,
                "zoom_factor": 0,
                "channel_averaging_map": [[0, 2], [744, 0]],
                "channel_offset": 0,
                "output_link_map": [[0, 0], [200, 1]],
            },
            {
                "fsp_id": 2,
                "function_mode": "CORR",
                "frequency_slice_id": 2,
                "integration_factor": 1,
                "zoom_factor": 1,
                "zoom_window_tuning": 650000,
                "channel_averaging_map": [[0, 2], [744, 0]],
                "channel_offset": 744,
                "output_link_map": [[0, 4], [200, 5]],
                "output_host": [[0, "192.168.1.1"]],
                "output_port": [[0, 9744, 1]],
            },
        ],
        "vlbi": {},
    },
    "pss": {},
    "pst": {},
    "pointing": {
        "target": {
            "system": "ICRS",
            "target_name": "Polaris Australis",
            "ra": "21:08:47.92",
            "dec": "-88:57:22.9",
        }
    },
}
