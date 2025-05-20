"""."""

import logging

import pytest
import yaml
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


@pytest.mark.requires_talons_on
@pytest.mark.hw_in_the_loop
def test_qspi_version():
    """Check QSPI version.

    Check whether the QSPI version on each ITF CBF Talon Board is the expected version.
    """
    # Get CBF Talon IPs
    hw_config_relative_path = "resources/mcs/hw_config.yaml"
    talon_board_hw_config = {}

    with open(hw_config_relative_path, "r") as f:
        talon_board_hw_config = yaml.safe_load(f)["talon_board"]

    # Get CBF Engineering console version
    umbrella_chart_relative_path = "charts/ska-mid-itf-sut/Chart.yaml"
    with open(umbrella_chart_relative_path, "r") as f:
        sut_chart = yaml.safe_load(f)

        for dependency in sut_chart["dependencies"]:
            if dependency["name"] == "ska-mid-cbf-engineering-console":
                cbf_engineering_console_version = dependency["version"]
                break

    fpga_bitstream_version = TalonBoardCommandExecutor.get_fpga_bitstream_version(
        cbf_engineering_console_version
    )
    logger.info(f"FPGA bitstream version: {fpga_bitstream_version}")

    user = "root"

    # Get actual QSPI version from talonboards and compare with expected version
    for talon_board in talon_board_hw_config.keys():
        ip = talon_board_hw_config[talon_board]

        talon_board_command_executor = TalonBoardCommandExecutor(ip, user)
        command_result = talon_board_command_executor.execute_command(
            talon_board, "qspi_version_check"
        )
        if command_result is None:
            pytest.fail(f"Failed to execute command successfully on Talon board {talon_board}")

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

        qspi_version_compatible = TalonBoardCommandExecutor.check_qspi_version(
            fpga_bitstream_version, qspi_version
        )

        assert qspi_version_compatible, (
            f"QSPI version {qspi_version} loaded on Talon board {talon_board} is not compatible "
            f"with FPGA bitstream version {fpga_bitstream_version}"
        )
