"""."""

import hashlib
import logging
import os

import pytest
import yaml
from tango import DeviceProxy

from utils.talon_communication import TalonBoardCommandExecutor

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def settings():
    """Fixture to set up the test environment.

    :return: Smoke test configuration
    :rtype: Dict
    """
    settings = {}

    # Path where the CBF EC clone PVC volume is mounted
    CBF_EC_MOUNT_PATH = os.environ.get("CBF_EC_MOUNT_PATH", "/app/cbf-ec")

    # Get CBF Talon IPs
    hw_config_relative_path = "resources/mcs/hw_config.yaml"
    with open(hw_config_relative_path, "r") as f:
        talon_board_ips = yaml.safe_load(f)["talon_board"]

    settings["talon_board_ips"] = talon_board_ips

    settings["cbf_ec_mount_path"] = CBF_EC_MOUNT_PATH

    # Get SPFRX IPs

    # Populate settings object with spfrx talon board ips
    # settings["spfrx_talon_board_ips"] = ""

    return settings


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
def test_qspi_bitstream_compatibility(settings):
    """Check QSPI bitstream version.

    Check whether the firmware version on each ITF CBF Talon Board is the expected version.

    :param settings: Smoke test configuration
    :type settings: Dict
    """
    talon_board_ips = settings["talon_board_ips"]

    # Get CBF Engineering console version and expected fpga bitstream version
    umbrella_chart_relative_path = "charts/ska-mid/Chart.yaml"
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

    # Generate CBF bitstream MD5 checksum (expected bitstream checksum)
    rpd_dir = f"{settings['cbf_ec_mount_path']}/fpga-talon/bin"
    rpd_path = f"{rpd_dir}/talon_dx-tdc_base-tdc_vcc_processing-application.hps.rpd"
    bitstream_md5_hash = hashlib.md5()
    with open(rpd_path, "rb") as rpd_file:
        raw_data = rpd_file.read()
        bitstream_md5_hash.update(raw_data)
    bitstream_checksum = bitstream_md5_hash.hexdigest()
    logger.info(f"Expected bitstream checksum: {bitstream_checksum}")

    user = "root"

    # Get actual bitstream version from talonboards and compare with expected version
    for talon_board, ip in talon_board_ips.items():
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

        # Get bitstream version at slot
        loaded_bitstream_version = talon_board_command_executor.get_loaded_bitstream_version(
            slot_number, command_result
        )
        if loaded_bitstream_version is None:
            pytest.fail(f"Failed to get bitstream version on Talon board {talon_board}")

        logger.info(f"Talon {talon_board} bitstream version: {loaded_bitstream_version}")

        # Get actual bitstream checksum reported at talon slot
        loaded_bitstream_checksum = talon_board_command_executor.get_bitstream_checksum(
            slot_number, command_result
        )
        if loaded_bitstream_checksum is None:
            pytest.fail(f"Failed to get bitstream checksum on Talon board {talon_board}")
        logger.info(f"Talon {talon_board} bitstream checksum: {loaded_bitstream_checksum}")

        # Check compatibility
        bitstream_compatible = TalonBoardCommandExecutor.check_bitstream_compatibility(
            fpga_bitstream_version,
            loaded_bitstream_version,
            bitstream_checksum,
            loaded_bitstream_checksum,
        )

        assert bitstream_compatible, (
            f"Bitstream compatibility check failed for Talon board {talon_board}. "
            f"Checksum computed from CBF EC: {bitstream_checksum}, "
            f"Checksum reported on Talon board slot {slot_number}: {loaded_bitstream_checksum}. "
        )


def test_spfrx_qspi_bitstream_compatibility(settings):
    """Check QSPI bitstream version for SPFRX Talon Boards.

    :param settings: Smoke test configuration
    :type settings: Dict
    """
    # spfrx_talon_board_ips = settings["spfrx_talon_board_ips"]

    # Get CBF Engineering console version from charts/ska-mid/Chart.yaml

    # Get actual bitstream version from talonboards and compare with expected version

    # Get currently loaded slot (talon_board_command_executor.get_currently_loaded_slot())

    # Get bitstream version at slot (talon_board_command_executor.get_loaded_bitstream_version())

    # Check compatibility (talon_board_command_executor.check_spfrx_bitstream_compatibility())

    # bitstream_compatible = expected == actual_loaded

    # assert bitstream_compatible
    pass
