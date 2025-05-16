import ast
import os
import re
import sys
from datetime import datetime
from typing import Callable, Match, Optional

# Local imports
from scripts.sequence_diagrammer.plantuml_helper import PlantUMLSequenceDiagram

# Submodule imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory of the script
SUBMODULE_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../.jupyter-notebooks/src"))
sys.path.append(SUBMODULE_PATH)

from notebook_tools.sequence_diagram_setup import (
    # Regex patterns
    LOG_LRC_RESULT_REGEX_PATTERN,
    INVOKE_EXECUTE_COMMAND_REGEX_PATTERN,
    DEBUG_PATCH_FORWARD_REGEX_PATTERN,
    K_VALUES_TO_DISH_REGEX_PATTERN,
    CSP_SDP_ON_OFF_COMMAND_REGEX_PATTERN,
    INVOKING_COMMAND_REGEX_PATTERN,
    COMMAND_INVOKED_REGEX_PATTERN,
    CSP_SDP_RELEASE_RESOURCES_COMMAND_REGEX_PATTERN,
    INCOMING_COMMAND_CALL_REGEX_PATTERN,
    RETURN_COMMAND_CALL_REGEX_PATTERN,
    # Constants
    TRACK_LOAD_TABLE_LIMIT,
    # Functions
    get_cleaned_device_name,
)


class LogParserHelper:
    '''Class with log parsing helper functions'''
    def __init__(
        self,
        sequence_diagram: PlantUMLSequenceDiagram,
        get_likely_caller_from_hierarchy: Callable[[str], str],
        include_dividers: bool,
        use_new_pages: bool,
        include_absolute_timestamps: bool,
        include_relative_timestamps: bool,
    ):
        self.sequence_diagram = sequence_diagram
        self.get_likely_caller_from_hierarchy = get_likely_caller_from_hierarchy

        self.include_dividers = include_dividers
        self.use_new_pages = use_new_pages
        self.include_absolute_timestamps = include_absolute_timestamps
        self.include_relative_timestamps = include_relative_timestamps

        self.track_load_table_count = 0
        self.brand_new_diagram = True
        self.current_timestamp = datetime.now()
        self.current_reference_timestamp = datetime.now()
        self.reference_timestamp_set = False
        self.fresh_reference_timestamp = True

    def handle_lrc_result_log(self, cleaned_device: str, message: str):
        '''Handles parsing of longRunningCommandResult logs and updates the sequence diagram'''
        match = LOG_LRC_RESULT_REGEX_PATTERN.search(message)
        if match:
            from_device = match.group(1).strip()
            command_id = match.group(2).strip()
            status = match.group(3).strip()

            # Ignore staging statuses for cleaner diagrams
            if status.lower() == 'staging':
                return

            # Remove ID from command
            # 1731336386.5340867_71131397947360_LoadDishCfg to LoadDishCfg
            command = command_id.split('_')[-1]

            # Clean the target device name for PlantUML
            cleaned_from_device = get_cleaned_device_name(from_device)

            # Add an arrow to the sequence diagram
            self.sequence_diagram.add_command_response(
                cleaned_from_device, cleaned_device, f'""{command}"" -> {status}'
            )

    def handle_invoke_or_execute_command_log(self, cleaned_device: str, message: str):
        '''Handles parsing of invoke_command and execute_command logs and updates the sequence diagram'''
        match = INVOKE_EXECUTE_COMMAND_REGEX_PATTERN.search(message)
        if match:
            command_name = match.group(1).strip()

            # Exclude spammy commands from the diagram
            if command_name in ['MonitorPing', 'TrackLoadTable']:
                return

            self.generic_command_match_handling(match, cleaned_device)

    def handle_debug_patch_log(self, cleaned_device: str, message: str, actors: list,):
        '''Handles parsing of _debug_patch logs and updates the sequence diagram'''
        match = DEBUG_PATCH_FORWARD_REGEX_PATTERN.search(message)
        if match:
            target_class = match.group(1)
            command_name = match.group(2)

            # Use the device hierarchy to get the likely caller
            likely_caller = self.get_likely_caller_from_hierarchy(cleaned_device)

            # Most of these logs are directly called from the notebook
            # Small trick for setting the notebook as the caller for all mid subarray calls
            if target_class == 'SubarrayNodeMid':
                likely_caller = self.get_likely_caller_from_hierarchy(likely_caller)

            # Use new pages for major notebook commands to split the images
            if (
                self.use_new_pages or self.include_relative_timestamps
            ) and likely_caller in actors:
                # Use major commands as time reference points
                self.current_reference_timestamp = self.current_timestamp
                # We don't want a new page on the very first command
                # Only split on the major commands that either come from test to
                # central node, or from central node to subarray node
                if not self.brand_new_diagram and target_class in ("MidTmcCentralNode", "MidTmcSubarray"):
                    self.sequence_diagram.add_new_page(command_name)

                self.brand_new_diagram = False
                self.fresh_reference_timestamp = True

            # Create a divider if a new notebook command was run
            if self.include_dividers and likely_caller in actors:
                self.sequence_diagram.add_divider(command_name)

            note = f'""{target_class}.{command_name}""'
            note = self.format_note_with_timestamp(note)

            # Add an arrow to the sequence diagram from the likely caller to the target device
            self.sequence_diagram.add_command_call(
                likely_caller, cleaned_device, note
            )

    def handle_set_k_numbers_to_dish_log(self, cleaned_device: str, message: str):
        '''Handles parsing of _set_k_numbers_to_dish logs and updates the sequence diagram'''
        match = K_VALUES_TO_DISH_REGEX_PATTERN.search(message)
        if match:
            self.generic_command_match_handling(match, cleaned_device)

    def handle_csp_sdp_invoking_on_off_command_log(self, cleaned_device: str, message: str):
        '''Handles parsing turn_on_csp and turn_on_sdp logs and updates the sequence diagram'''
        # this is not "On" or "Off" for the master device, but to get them to turn on/off the lower devices
        # Adjusting the text of the command going to the sequence diagram for clarity
        adjustment = 'for lower devices command'
        print(f'Message before: {message}')
        message = message.replace('command', adjustment)
        print(f'Message after: {message}')

        match = CSP_SDP_ON_OFF_COMMAND_REGEX_PATTERN.search(message)
        if match:
            print(f'{match.group(1)}')
            print(f'{match.group(2)}')
            self.generic_command_match_handling(match, cleaned_device)

    def handle_invoking_most_commands_log(self, cleaned_device: str, message: str):
        '''Handles parsing do_mid, call_adapter_method, assign_csp_resources and scan_dishes logs; 
        and updates the sequence diagram'''
        # There is one log that just says "... on SubarrayNode."
        non_standard_subarray_device_in_log = 'SubarrayNode.'   # these have full stops
        standardised_subarray_device = 'ska_mid/tm_subarray_node/1'

        if message.endswith(non_standard_subarray_device_in_log):
            message = message.replace(
                non_standard_subarray_device_in_log, standardised_subarray_device
            )

        # Some of these logs end with a full stop which then gets included in the device name
        if message.endswith('.'):
            message = message[:-1]

        match = INVOKING_COMMAND_REGEX_PATTERN.search(message)
        if match:
            # Some of the call_adapter_method have the full tango trl in the device name
            if match.group(2).startswith('tango:'):
                self.generic_command_match_handling(match, cleaned_device, 'full_trl')
            else:
                self.generic_command_match_handling(match, cleaned_device)
            return

        match = COMMAND_INVOKED_REGEX_PATTERN.search(message)
        if match:
            self.generic_command_match_handling(match, cleaned_device)

    def handle_csp_sdp_release_resources_command_log(self, cleaned_device: str, message: str):
        '''Handles release_csp_resources and release_sdp_resources logs and updates the sequence diagram'''
        match = CSP_SDP_RELEASE_RESOURCES_COMMAND_REGEX_PATTERN.search(message)
        if match:
            self.generic_command_match_handling(match, cleaned_device)

    def info_patch_cb(self, device, message, limit_track_load_table_calls: bool):
        if "->" in message:
            match = INCOMING_COMMAND_CALL_REGEX_PATTERN.search(message)
            if match:
                method = match.group(1)
                method = method.split(".")[1]

                # Reduce "TrackLoadTable" commands from the diagram
                if method == "TrackLoadTable":
                    self.track_load_table_count += 1
                    if (
                        limit_track_load_table_calls
                        and self.track_load_table_count > TRACK_LOAD_TABLE_LIMIT
                    ):
                        return

                caller = self.get_likely_caller_from_hierarchy(device)
                note = f'""{method}""'
                note = self.format_note_with_timestamp(note)

                self.sequence_diagram.add_command_call(caller, device, note)

        elif "<-" in message:
            match = RETURN_COMMAND_CALL_REGEX_PATTERN.search(message)
            if match:
                return_val = match.group(1)
                method = match.group(2)
                method = method.split(".")[1]

                # Reduce "TrackLoadTable" commands from the diagram
                if method == 'TrackLoadTable':
                    self.track_load_table_count += 1
                    if (
                        limit_track_load_table_calls
                        and self.track_load_table_count > TRACK_LOAD_TABLE_LIMIT
                    ):
                        return

                # The ResultCode.QUEUED logs seem to be delayed and duplicated so exclude them
                if 'ResultCode.QUEUED' in return_val:
                    return

                caller = self.get_likely_caller_from_hierarchy(device)

                note = f'""{method}"" -> {return_val}'
                note = self.format_note_with_timestamp(note)

                self.sequence_diagram.add_command_response(
                    device, caller, note
                )

    def component_state_update_cb(self, device, message):
        search_string = r"Updating (\w*) (\w*) component state with \[(.*)\]"

        match = re.search(search_string, message)

        if match:
            string_dict = match.group(3)
            string_dict = string_dict.replace("<", "'<")
            string_dict = string_dict.replace(">", ">'")
            component_state_updates = ast.literal_eval(string_dict)

            note_text = "Component state update"
            for attr, attr_value in component_state_updates.items():
                note_text += f'\n""{attr} = {attr_value}""'.encode("unicode_escape").decode(
                    "utf-8"
                )
            self.sequence_diagram.add_hexagon_note_over(device, note_text)

    def generic_command_match_handling(
        self, match: Match[str], cleaned_device: str, target_device_type: str='none'
    ):
        '''Handle a generic command with target device and add it to the sequence diagram'''
        command_name = match.group(1).strip()
        target_device = match.group(2).strip()

        # Clean the target device name for PlantUML
        cleaned_target_device = get_cleaned_device_name(target_device, target_device_type)

        note = f'""{command_name}""'
        note = self.format_note_with_timestamp(note)

        # Add an arrow to the sequence diagram
        self.sequence_diagram.add_command_call(
            cleaned_device, cleaned_target_device, note
        )

    def format_timestamp(self, timestamp_dt: datetime) -> str:
        '''Format a datetime object into a string with millisecond precision'''
        timestamp_str = (
            timestamp_dt.strftime('%Y-%m-%dT%H:%M:%S') + f'.{timestamp_dt.microsecond // 1000:03d}'
        )
        return timestamp_str

    def format_timestamp_delta(self, current: datetime, reference: datetime) -> str:
        '''Return the time delta between two datetimes as a +X.XXXs string'''
        delta_dt = current - reference
        delta_str = f'+{delta_dt.total_seconds():.3f}s'
        return delta_str

    def format_note_with_timestamp(self, note: str) -> str:
        '''Add absolute or relative timestamp prefix to a note based on configuration'''
        if not self.reference_timestamp_set:
            # Set the reference to the first timestamp drawn in the puml
            self.current_reference_timestamp = self.current_timestamp
            self.reference_timestamp_set = True

        if self.include_relative_timestamps and not self.fresh_reference_timestamp:
            delta_str = self.format_timestamp_delta(
                self.current_timestamp, self.current_reference_timestamp
            )
            note = f'{delta_str}\n{note}'

        elif self.include_absolute_timestamps or self.fresh_reference_timestamp:
            timestamp_str = self.format_timestamp(self.current_timestamp)
            note = f'{timestamp_str}\n{note}'
            self.fresh_reference_timestamp = False

        return note

    def set_current_timestamp(self, timestamp_dt: datetime):
        '''Set the current_timestamp class variable'''
        self.current_timestamp = timestamp_dt
