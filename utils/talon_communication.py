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
    qspi_check_command = "qspi_partition.sh -i"
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

    def get_qspi_version(self, slot_number: str, qspi_check_command_result: str):
        """Determine the QSPI version loaded at the given slot (partition)"""
        qspi_version_pattern = rf"partition\{{{slot_number}\}}_hash,[^_]*_version:(.*)"
        qspi_version_match = re.search(qspi_version_pattern, qspi_check_command_result)
        if qspi_version_match:
            qspi_version = qspi_version_match.group(1)
        else:
            error_string = f"Failed to find QSPI version in result: {qspi_check_command_result}"
            logger.error(error_string)
            return None

        return qspi_version

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

        fpga_bitstream_version = talondx_boardmap["fpga_bitstreams"][0]["version"]

        return fpga_bitstream_version

    @staticmethod
    def check_qspi_version(fpga_bitstream_version: str, actual_qspi_version: str):
        """Determines if bitstream version is compatible with the QSPI version.

        Compares fpga_bitstream version with the QSPI version loaded on the Talon board to
        determine compatibility. Returns True if they are compatible.
        """
        # Dropping patch version. QSPI version expected to match only major and minor version of
        # of the fpga bitstream version going forward.
        major, minor, *_ = fpga_bitstream_version.split(".")
        expected_qspi_major_minor = f"{major}.{minor}"
        major, minor, *_ = actual_qspi_version.split(".")
        actual_qspi_major_minor = f"{major}.{minor}"

        # TODO: Remove once the agreed upon version compatibility is provided
        if fpga_bitstream_version == "1.1.0" and actual_qspi_version == "1.0.1":
            return True

        return expected_qspi_major_minor == actual_qspi_major_minor
