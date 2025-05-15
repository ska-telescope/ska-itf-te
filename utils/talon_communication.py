import re
import subprocess
import logging

logger = logging.getLogger(__name__)


class TalonBoardCommandExecutor:
    """Convenience class to execute commands on Talon boards."""

    command_map = {
        "qspi_version_check": "qspi_partition.sh -i",
    }
    qspi_check_command = "qspi_partition.sh -i"
    slot_number_pattern = r"Currently loaded slot: (\d+)"

    def __init__(self, ip: str, user: str):
        """Initializes the TalonBoardCommandExecutor with the IP and user for SSH."""
        self.ip = ip
        self.user = user

    def execute_command(self, talon_board: str, command_name: str, timeout: int = 10):
        """Executes a command on the Talon board over SSH."""

        command = self.get_command(command_name)

        try:
            result = subprocess.run(
                ["ssh", f"{self.user}@{self.ip}", command], capture_output=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            error_string = f"Could not communicate with Talon board {talon_board}"
            logger.error(error_string)
            return None
        except Exception as e:
            error_string = f"Failed to run command successfully on Talon board {talon_board}: {e}"
            logger.error(error_string)
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
