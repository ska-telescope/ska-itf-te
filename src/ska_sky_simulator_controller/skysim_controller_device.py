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
from ska_sky_simulator_controller.skysim_controller_component_manager import (
    SkysimControllerComponentManager,
)

__all__ = ["SkysimControllerDevice", "main"]


class SkysimControllerDevice(TestEquipmentBaseDevice):
    """A Tango device for monitor and control of a Skysim Controller."""

    # --------------
    # Initialization
    # --------------
    def create_component_manager(
        self,
    ) -> SkysimControllerComponentManager:
        """
        Create and return a component manager for this device.

        :return: a component manager for this device.
        """
        self.logger.info("Create component manager for %s", self.Model)
        # pylint: disable-next=attribute-defined-outside-init
        self._interface_definition = InterfaceDefinitionFactory()(self.Model)
        return SkysimControllerComponentManager(
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
    Launch a `SkysimController` server instance.

    :param args: arguments to the sky simulator controller device.
    :param kwargs: keyword arguments to the server

    :returns: the Tango server exit code
    """
    return tango.server.run(  # pragma: no cover
        (SkysimControllerDevice,), args=args, **kwargs
    )


if __name__ == "__main__":
    main()  # pragma: no cover
