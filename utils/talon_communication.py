import logging
import re
import subprocess

import requests

logger = logging.getLogger(__name__)


class TalonBoardCommandExecutor:
    """Convenience class to execute commands on Talon boards."""

    command_map = {
        "qspi_version_check": "qspi_partition.sh -i",
    }

    slot_number_pattern = r"Currently loaded slot: (\d+)"

    def __init__(self, ip: str, user: str):

        self.ip = ip
        self.user = user

    def execute_command(self, talon_board: str, command_name: str, timeout: int = 10):
        """Executes a command on the Talon board over SSH."""

        command = self.get_command(command_name)

        try:
            result = subprocess.run(
                [
                    "ssh",
                    f"{self.user}@{self.ip}",
                    "-o StrictHostKeyChecking=no",
                    "-o HostKeyAlgorithms=+ssh-rsa",
                    "-o PubkeyAcceptedAlgorithms=+ssh-rsa",
                    command,
                ],
                capture_output=True,
                timeout=timeout,
            )
            logger.debug(result)
        except subprocess.TimeoutExpired:
            error_string = f"Could not communicate with Talon board {talon_board}"
            logger.error(error_string)
            return None
        except PermissionError:
            error_string = f"Permission denied when trying to access Talon board {talon_board}"
            logger.error(error_string)
            return None
        except Exception as e:
            error_string = f"Failed to run command successfully on Talon board {talon_board}: {e}"
            logger.error(error_string)
            return None

        if result.returncode != 0:
            logger.error(
                f"Failed to run command successfully on Talon board {talon_board}: "
                f"{result.stderr.decode()}"
            )
            return None

        result_string = result.stdout.decode()

        return result_string

    def get_command(self, command_name: str):
        """Uses command name to get the command string from the command map."""
        if command_name not in self.command_map:
            logger.error(f"Command {self.command} not found in command map. Check command name.")
            return None

        return self.command_map[command_name]

    def get_currently_loaded_slot(self, qspi_check_command_result: str):
        """Determine the currently loaded slot (partition)."""
        slot_number_match = re.search(self.slot_number_pattern, qspi_check_command_result)
        if slot_number_match:
            slot_number = slot_number_match.group(1)
        else:
            error_string = f"Failed to find slot number in result: {qspi_check_command_result}"
            logger.error(error_string)
            return None

        return slot_number

    def get_loaded_bitstream_version(self, slot_number: str, qspi_check_command_result: str):
        """Determine the QSPI version loaded at the given slot (partition)"""
        qspi_version_pattern = rf"partition\{{{slot_number}\}}_version,.*-(\d+\.\d+\.\d+)"
        legacy_qspi_version_pattern = rf"partition\{{{slot_number}\}}_hash,[^_]+_version:(\d+\.\d+\.\d+)"
        version_pattern = r'\d+\.\d+\.\d+'
        is_legacy = False

        qspi_version_match = re.search(qspi_version_pattern, qspi_check_command_result)

        # Check if the version is reported in legacy form
        if not qspi_version_match:
            qspi_version_match = re.search(legacy_qspi_version_pattern, qspi_check_command_result)

        if qspi_version_match:
            qspi_version = qspi_version_match.group(1)
        else:
            error_string = f"Failed to find QSPI version in result: {qspi_check_command_result}"
            logger.error(error_string)
            return None

        # Check that a valid version was retrieved
        if not re.fullmatch(version_pattern, qspi_version):
            error_string = f"QSPI version could not be parsed correctly"
            logger.error(error_string)
            return None

        return qspi_version
    
    def get_bitstream_checksum(self, slot_number: str, qspi_check_command_result: str):
        bitstream_checksum_pattern = rf"partition\{{{slot_number}\}}_hash,([a-fA-F0-9]+)(?:_version:\d+\.\d+\.\d+)?"
        bitstream_checksum_match = re.search(bitstream_checksum_pattern, qspi_check_command_result)

        if bitstream_checksum_match:
            bitstream_checksum = bitstream_checksum_match.group(1)
        else:
            error_string = f"Failed to find Bitstream hash in result: {qspi_check_command_result}"
            logger.error(error_string)
            return None

        return bitstream_checksum      

    @staticmethod
    def get_fpga_bitstream_version(cbf_engineering_console_version: str) -> str:
        """Determine the expected QSPI version based on the FPGA bitstream version.

        For compatibility the QSPI version shall match the Major and Minor version of the FPGA
        bitstream. The FPGA bitstream version is fetched from the talondx_boardmap.json file in the
        CBF engineering console repo given the version of the CBF engineering console deployed.
        """
        talondx_boardmap_link = (
            "https://gitlab.com/ska-telescope/ska-mid-cbf-engineering-console"
            f"/-/raw/{cbf_engineering_console_version}/src/ska_mid_cbf_engineering_console"
            "/deployer/talondx_config/talondx_boardmap.json"
        )

        response = requests.get(talondx_boardmap_link, timeout=5)

        if response.status_code != 200:
            error_string = f"Failed to fetch talondx_boardmap.json from {talondx_boardmap_link}"
            logger.error(error_string)
            return None

        try:
            talondx_boardmap = response.json()
        except ValueError:
            error_string = f"Failed to parse talondx_boardmap.json: {response.text}"
            logger.error(error_string)
            return None

        fpga_bitstream_version = next(
            (
                bitstream_info["version"]
                for bitstream_info in talondx_boardmap["fpga_bitstreams"]
                if bitstream_info["fsp_mode"] == "corr"
            ),
            None,
        )

        return fpga_bitstream_version

    @staticmethod
    def check_bitstream_compatibility(expected_bitstream_version: str, actual_bitstream_version: str, expected_bitstream_checksum: str, actual_bitstream_checksum: str):
        """Applies the logic to determine if the CBF software is compatible with the Talon firmware.

        Compares fpga_bitstream version with the QSPI version loaded on the Talon board to
        determine compatibility. Logs a warning if the versions are not compatible.

        Compares the expected bitstream checksum with the actual bitstream checksum reported on the Talon board.
        Returns True if the versions are compatible, False otherwise.
        """
        # Dropping patch version. QSPI version expected to match only major and minor version of
        # of the fpga bitstream version going forward.
        major, minor, *_ = expected_bitstream_version.split(".")
        expected_bitstream_major_minor = f"{major}.{minor}"
        major, minor, *_ = actual_bitstream_version.split(".")
        actual_bitstream_major_minor = f"{major}.{minor}"

        version_based_compatibility = (expected_bitstream_major_minor == actual_bitstream_major_minor)

        # TODO: Remove once the agreed upon version compatibility is provided
        if expected_bitstream_version == "1.1.0" and actual_bitstream_version == "1.0.1":
            version_based_compatibility = True

        if not version_based_compatibility:
            logger.warning(
                f"Version based compatibility check failed. Expected bitstream version: {expected_bitstream_version}, Talon allowed bitstream version: {actual_bitstream_version}"
            )
        
        bitstream_checksum_based_compatibility = (actual_bitstream_checksum == expected_bitstream_checksum)

        return bitstream_checksum_based_compatibility