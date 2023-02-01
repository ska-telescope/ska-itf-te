# -*- coding: utf-8 -*-
#
# (c) 2022 CSIRO.
#
# Distributed under the terms of the CSIRO Open Source Software Licence
# Agreement
# See LICENSE.txt for more info.

"""Monitoring and control of a Sky Simulator Controller module."""
from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Dict, Final, Optional, Tuple

from ska_control_model.power_state import PowerState
from ska_control_model.task_status import TaskStatus
from ska_ser_test_equipment.scpi import (
    AttributeClient,
    AttributeRequest,
    AttributeResponse,
    InterfaceDefinitionType,
    ScpiBytesClientFactory,
    ScpiClient,
    SupportedProtocol,
)
from ska_tango_base.poller import PollingComponentManager


# pylint: disable-next=too-many-instance-attributes
class SkySimulatorControllerComponentManager(
    PollingComponentManager[AttributeRequest, AttributeResponse]
):
    """A component manager for a sky simulator controller."""

    # pylint: disable-next=too-many-arguments
    def __init__(
        self,
        interface_definition: InterfaceDefinitionType,
        protocol: SupportedProtocol,
        host: str,
        port: int,
        logger: logging.Logger,
        communication_state_callback: Callable,
        component_state_callback: Callable,
        update_rate: float = 5.0,
    ) -> None:
        """
        Initialise a new sky simulator controller component manager instance.

        :param interface_definition: definition of the sky simulator
            controller's SCPI interface
        :param protocol: the network protocol to be used to communicate
            with the sky simulator controller
        :param host: the host name or IP address of the sky simulator
            controller.
        :param port: the port of the sky simulator controller.
        :param logger: a logger for this component manager to use for
            logging
        :param communication_state_callback: callback to be called when
            the status of communications between the component manager
            and its component changes.
        :param component_state_callback: callback to be called when the
            state of the component changes.
        :param update_rate: how often updates to attribute values should
            be provided. This is not necessarily the same as the rate at
            which the instrument is polled. For example, the instrument
            may be polled every 0.1 seconds, thus ensuring that any
            invoked commands or writes will be executed promptly.
            However, if the `update_rate` is 5.0, then routine reads of
            instrument values will only occur every 50th poll (i.e.
            every 5 seconds).
        """
        bytes_client = ScpiBytesClientFactory().create_client(
            protocol, host, port, interface_definition["timeout"]
        )
        scpi_client = ScpiClient(
            bytes_client, chain=interface_definition["supports_chains"]
        )
        self._attribute_client = AttributeClient(
            scpi_client, interface_definition["attributes"]
        )

        self._model = interface_definition["model"]
        self._max_tick: Final = int(
            update_rate / interface_definition["poll_rate"]
        )
        # We'll count ticks upwards, but start at the maximum so that
        # our initial update request occurs as soon as possible.
        self._tick = self._max_tick

        self._identified = False
        self._reset_status: Optional[TaskStatus] = None
        self._reset_callback: Optional[Callable] = None

        self._write_lock = threading.Lock()
        self._attributes_to_write: Dict[str, Any] = {}

        super().__init__(
            logger,
            communication_state_callback,
            component_state_callback,
            interface_definition["poll_rate"],
            identity=None,
            gpio_1=None,
            gpio_2=None,
            gpio_3=None,
            gpio_4=None,
            gpio_5=None,
            gpio_6=None,
            gpio_7=None,
        )

        self.logger.debug(
            f"Initialising sky simulator controller component manager: "
            f"Update rate is {update_rate}. "
            f"Poll rate is {interface_definition['poll_rate']}. "
            f"Attributes will be updated roughly each {self._max_tick} polls."
        )

    def off(
        self, task_callback: Optional[Callable] = None
    ) -> Tuple[TaskStatus, str]:
        """
        Turn the component off.

        :param task_callback: callback to be called when the status of
            the command changes

        :raises NotImplementedError: because this command is not yet
            implemented
        """
        raise NotImplementedError("The device cannot be turned off or on.")

    def standby(
        self, task_callback: Optional[Callable] = None
    ) -> Tuple[TaskStatus, str]:
        """
        Put the component into low-power standby mode.

        :param task_callback: callback to be called when the status of
            the command changes

        :raises NotImplementedError: because this command is not yet
            implemented
        """
        raise NotImplementedError(
            "The device cannot be put into standby mode."
        )

    def on(
        self, task_callback: Optional[Callable] = None
    ) -> Tuple[TaskStatus, str]:
        """
        Turn the component on.

        :param task_callback: callback to be called when the status of
            the command changes

        :raises NotImplementedError: because this command is not yet
            implemented
        """
        raise NotImplementedError("The device cannot be turned off or on.")

    def reset(
        self, task_callback: Optional[Callable] = None
    ) -> Tuple[TaskStatus, str]:
        """
        Reset the component (from fault state).

        :param task_callback: callback to be called when the status of
            the command changes

        :return: the task status and a message
        """
        self.logger.debug("Reset method called; setting status to QUEUED")
        self._reset_status = TaskStatus.QUEUED
        self._reset_callback = task_callback

        if task_callback is not None:
            task_callback(status=TaskStatus.QUEUED)

        return (
            TaskStatus.QUEUED,
            "Reset command will be executed at next poll",
        )

    def write_attribute(self, **kwargs: Any) -> None:
        """
        Update spectrum analyser attribute value(s).

        This doesn't actually immediately write to the spectrum analyser.
        It only stores the details of the requested write where it will
        be picked up by the next iteration of the polling loop.

        :param kwargs: keyword arguments specifying attributes to be
            written along with their corresponding value.
        """
        self.logger.debug(
            f"Registering attribute writes for next poll: {kwargs}"
        )
        with self._write_lock:
            self._attributes_to_write.update(kwargs)

    def poll(self, poll_request: AttributeRequest) -> AttributeResponse:
        """
        Poll the hardware.

        Connect to the hardware, write any values that are to be
        written, and then read all values.

        :param poll_request: specification of the reads and writes to be
            performed in this poll.

        :return: responses to queries in this poll
        """
        self.logger.debug("Poller is initiating next poll.")
        poll_response = self._attribute_client.send_receive(poll_request)
        self.logger.debug("Poller is returning result of next poll.")
        return poll_response

    def get_request(self) -> AttributeRequest:
        """
        Return the reads and writes to be executed in the next poll.

        :return: reads and writes to be executed in the next poll.
        """
        self.logger.debug("Constructing request for next poll.")
        self._tick += 1

        attribute_request = AttributeRequest()
        if not self._identified:
            self.logger.debug("Adding identity query.")
            attribute_request.set_queries("identity")
        elif self._reset_status == TaskStatus.QUEUED:
            self.logger.debug("Adding reset setops.")
            # attribute_request.add_setop("reset")
            # attribute_request.add_setop("frequency", 10000000.0)
            # attribute_request.add_setop("rf_output_on", False)
            self._reset_status = TaskStatus.IN_PROGRESS
            if self._reset_callback is not None:
                self._reset_callback(status=TaskStatus.IN_PROGRESS)
        else:
            with self._write_lock:
                for name, value in self._attributes_to_write.items():
                    self.logger.debug(
                        f"Adding write request setop: {name}={value}."
                    )
                    attribute_request.add_setop(name, value)
                self._attributes_to_write.clear()

            if self._tick > self._max_tick:
                self.logger.debug(f"Tick {self._tick} >= {self._max_tick}.")
                self.logger.debug("Adding queries.")
                # TODO: add set_queries
                attribute_request.set_queries(
                    "frequency",
                    #     "power_dbm",
                    #     "rf_output_on",
                    #     "query_error",
                    #     "device_error",
                    #     "execution_error",
                    #     "command_error",
                    #     "power_cycled",
                )
                self._tick = 0
        self.logger.debug("Returning request for next poll.")
        return attribute_request

    def poll_succeeded(self, poll_response: AttributeResponse) -> None:
        """
        Handle the receipt of new polling values.

        This is a hook called by the poller when values have been read
        during a poll.

        :param poll_response: response to the pool, including any values
            read.
        """
        super().poll_succeeded(poll_response)
        values = poll_response.responses
        self.logger.debug(f"Handing results of successful poll: {values}.")

        # TODO: For now, we base the fault status of this device on the
        # value of the "device_error" attribute.
        fault = values.get("device_error", False)
        self.logger.debug(f"Calculated fault status is {fault}.")

        if "identity" in values and self._check_identity(values["identity"]):
            self.logger.debug(f"Identity established: {values['identity']}.")
            self._identified = True

        if self._reset_status == TaskStatus.IN_PROGRESS:
            self.logger.debug("Reset command has been executed.")
            self._reset_status = None
            if self._reset_callback is not None:
                self._reset_callback(status=TaskStatus.COMPLETED)

        self.logger.debug("Pushing updates.")
        # TODO: Always-on device for now.
        self._update_component_state(
            power=PowerState.ON, fault=fault, **values
        )

    def _check_identity(self, identity: str) -> bool:
        """
        Check that the instrument model matches our expectations.

        :param identity: the identity reported by the instrument, in the
            form "make,model,serial_number,version".

        :return: whether the identity of the instrument matches
            our expectations.
        """
        _, model, _, _ = (s.strip() for s in identity.split(","))
        if model != self._model:
            self.logger.error(
                f"Expected instrument model to be {self._model},  but "
                f"it is {model}. Polling cannot proceed until this is "
                "corrected."
            )
            return False
        return True

    def polling_stopped(self) -> None:
        """
        Respond to polling having stopped.

        This is a hook called by the poller when it stops polling.
        """
        self.logger.debug("Polling has stopped.")
        self._identified = False
        # Set to max here so that if/when polling restarts, an update is
        # requested as soon as possible.
        self._tick = self._max_tick
        super().polling_stopped()
