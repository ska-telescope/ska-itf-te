# -*- coding: utf-8 -*-
#
# (c) 2022 CSIRO.
#
# Distributed under the terms of the CSIRO Open Source Software Licence
# Agreement
# See LICENSE.txt for more info.

"""Module providing a Tango device for a Sky Simulator Controller."""
from typing import Any

import tango
import tango.server

from ska_ser_test_equipment.base.base_device import TestEquipmentBaseDevice
from ska_ser_test_equipment.scpi import InterfaceDefinitionFactory

from .sky_sim_ctl_component_manager import (
    SkySimulatorControllerComponentManager,
)

__all__ = ["SkySimulatorControllerDevice", "main"]


class SkySimulatorControllerDevice(TestEquipmentBaseDevice):
    """A Tango device for monitor and control of a Sky Simulator Controller."""

    # --------------
    # Initialization
    # --------------
    def create_component_manager(
        self,
    ) -> SkySimulatorControllerComponentManager:
        """
        Create and return a component manager for this device.

        :return: a component manager for this device.
        """
        # pylint: disable-next=attribute-defined-outside-init
        self._interface_definition = InterfaceDefinitionFactory()(self.Model)
        return SkySimulatorControllerComponentManager(
            self._interface_definition,
            self.Protocol,
            self.Host,
            self.Port,
            self.logger,
            self._communication_state_changed,
            self._component_state_changed,
            update_rate=self.UpdateRate,
        )


# ----------
# Run server
# ----------
def main(args: Any = None, **kwargs: Any) -> int:
    """
    Launch a `SkySimulatorController` server instance.

    :param args: arguments to the sky simulator controller device.
    :param kwargs: keyword arguments to the server

    :returns: the Tango server exit code
    """
    return tango.server.run(
        (SkySimulatorControllerDevice,), args=args, **kwargs
    )


if __name__ == "__main__":
    main()
