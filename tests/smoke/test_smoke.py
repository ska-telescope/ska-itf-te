"""."""

import logging
import yaml
import pytest
import os

from tango import DeviceProxy

from utils.talon_communication import TalonBoardCommandExecutor


logger = logging.getLogger(__name__)


def test_devices_reachable():
    """Tests connectivity to tango devices.

    This is a simple smoke test to check if the required devices are reachable.
    It creates device proxies to various tango devices and checks if they are reachable.
    """
    device = DeviceProxy(
        "tango-databaseds.ska-mid-central-controller.svc.mid.internal.skao.int"
        ":10000/mid-tmc/central-node/0"
    )

    assert device.ping(), "Device is not reachable"
    logger.info("Devices reachable")


@pytest.mark.hw_in_the_loop
def test_qspi_version():
    """Checked whether the QSPI version on each Talon Board is the expected version."""
    # Get CBF Talon IPs
    cwd = os.getcwd()
    hw_config_path = f"{cwd}/resources/mcs/hw_config.yaml"
    talon_board_hw_config = {}

    with open(hw_config_path, "r") as f:
        talon_board_hw_config = yaml.safe_load(f)["talon_board"]

    # TODO: Get bitstream version from spfrx_boardmap.json
    expected_qspi_version = "1.0.1"

    # Get actual QSPI version from talonboards
    user = "root"

    for talon_board in talon_board_hw_config.keys():
        ip = talon_board_hw_config[talon_board]

        talon_board_command_executor = TalonBoardCommandExecutor(ip, user)
        command_result = talon_board_command_executor.execute_command(
            talon_board, "qspi_version_check"
        )
        if command_result is None:
            pytest.fail(f"Failed to execute command on Talon board {talon_board}")

        # Get currently loaded slot
        slot_number = talon_board_command_executor.get_currently_loaded_slot(command_result)
        if slot_number is None:
            pytest.fail(f"Failed to get currently used slot on Talon board {talon_board}")

        logger.info(f"Talon {talon_board} loaded slot: {slot_number}")

        # Get QSPI version at slot
        qspi_version = talon_board_command_executor.get_qspi_version(slot_number, command_result)
        if qspi_version is None:
            pytest.fail(f"Failed to get QSPI version on Talon board {talon_board}")

        logger.info(f"Talon {talon_board} QSPI version: {qspi_version}")

        assert qspi_version == expected_qspi_version, (
            f"Expected Talon board {talon_board} QSPI version {expected_qspi_version}"
            f", but got {qspi_version}"
        )
