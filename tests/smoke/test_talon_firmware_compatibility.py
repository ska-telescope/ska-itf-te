"""."""

import hashlib
import logging
import os

import pytest
import yaml

from utils.talon_communication import TalonBoardCommandExecutor

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def talon_firmware_compatibility_settings():
    """Fixture to set up the test environment.

    :return: Smoke test configuration
    :rtype: Dict
    """
    talon_firmware_compatibility_settings = {}

    # Path where the CBF EC clone PVC volume is mounted
    CBF_EC_MOUNT_PATH = os.environ.get("CBF_EC_MOUNT_PATH", "/app/cbf-ec")

    # Get CBF Talon IPs
    hw_config_relative_path = "resources/mcs/hw_config.yaml"
    with open(hw_config_relative_path, "r") as f:
        talon_board_ips = yaml.safe_load(f)["talon_board"]

    talon_firmware_compatibility_settings["talon_board_ips"] = talon_board_ips

    talon_firmware_compatibility_settings["cbf_ec_mount_path"] = CBF_EC_MOUNT_PATH

    # Get SPFRX IPs
    spfrx_hw_config_relative_path = "resources/spfrx/spfrx_hw_config.yaml"
    with open(spfrx_hw_config_relative_path, "r") as f:
        spfrx_talon_board_ips = yaml.safe_load(f)["talon_board"]

    talon_firmware_compatibility_settings["spfrx_talon_board_ips"] = spfrx_talon_board_ips

    return talon_firmware_compatibility_settings


@pytest.mark.requires_talons_on
@pytest.mark.hw_in_the_loop
def test_qspi_bitstream_compatibility(talon_firmware_compatibility_settings):
    """Check QSPI bitstream version.

    Check whether the firmware version on each ITF CBF Talon Board is the expected version.

    :param talon_firmware_compatibility_settings: Smoke test configuration
    :type talon_firmware_compatibility_settings: Dict
    """
    settings = talon_firmware_compatibility_settings

    talon_board_ips = settings["talon_board_ips"]

    # Get CBF Engineering console version and expected fpga bitstream version
    umbrella_chart_relative_path = "charts/ska-mid/Chart.yaml"
    cbf_engineering_console_version = get_chart_dependency_version(
        umbrella_chart_relative_path, "ska-mid-cbf-engineering-console"
    )

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


@pytest.mark.skip(reason="Test fails in pipelines. Awaiting resolution of bug AT-3329")
@pytest.mark.requires_talons_on
def test_spfrx_qspi_bitstream_compatibility(talon_firmware_compatibility_settings):
    """Check QSPI bitstream version for SPFRX Talon Boards.

    :param talon_firmware_compatibility_settings: Smoke test configuration
    :type talon_firmware_compatibility_settings: Dict
    """
    settings = talon_firmware_compatibility_settings

    spfrx_talon_board_ips = settings["spfrx_talon_board_ips"]

    # Get SPFRx console version from charts/ska-mid/Chart.yaml
    umbrella_chart_relative_path = "charts/ska-mid/Chart.yaml"
    spfrx_talondx_console_version = get_chart_dependency_version(
        umbrella_chart_relative_path, "ska-mid-dish-spfrx-talondx-console"
    )

    spfrx_bitstream_version = TalonBoardCommandExecutor.get_spfrx_bitstream_version(
        spfrx_talondx_console_version
    )
    logger.info(f"FPGA bitstream version: {spfrx_bitstream_version}")

    # Get actual bitstream version from talonboards and compare with expected version
    user = "root"
    for talon_board, ip in spfrx_talon_board_ips.items():
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
        logger.info(f"SPFRx Talon {talon_board} bitstream version: {loaded_bitstream_version}")

        # Check compatibility
        bitstream_compatible = TalonBoardCommandExecutor.check_spfrx_bitstream_compatibility(
            loaded_bitstream_version,
            spfrx_bitstream_version,
        )

        assert bitstream_compatible


def get_chart_dependency_version(umbrella_chart_relative_path: str, dependency_name: str):
    """Get dependency version from umbrella chart.

    :param umbrella_chart_relative_path: Path (relative to repo root) to the umbrella chart
    :type umbrella_chart_relative_path: str
    :param dependency_name: Name of the dependency to look for
    :type dependency_name: str
    :return: Version of the dependency, returns None if not found
    :rtype: str | None
    """
    version = None
    with open(umbrella_chart_relative_path, "r") as f:
        chart = yaml.safe_load(f)

        for dependency in chart["dependencies"]:
            if dependency["name"] == dependency_name:
                version = dependency["version"]
                break

    return version
