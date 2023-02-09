"""Monitoring and control of a skysimulator controller package."""
__all__ = [
    "SkySimulatorControllerComponentManager",
    "SkySimulatorControllerDevice",
    "SkySimulatorControllerSimulator",
]

# TODO: parse the root-located .release file for the actual version
__version__ = "0.1.0"

from .sky_sim_ctl_component_manager import (
    SkySimulatorControllerComponentManager,
)
from .sky_sim_ctl_device import SkySimulatorControllerDevice
from .sky_sim_ctl_simulator import SkySimulatorControllerSimulator
