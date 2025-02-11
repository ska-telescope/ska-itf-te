import os
import re
import sys
from typing import Callable, Match, Optional

# Local imports
from scripts.sequence_diagrammer.plantuml_helper import PlantUMLSequenceDiagram

# Submodule imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory of the script
SUBMODULE_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../.jupyter-notebooks/src"))
sys.path.append(SUBMODULE_PATH)

from notebook_tools.sequence_diagram_setup import *
    
class LogParserHelper:
    '''Class with log parsing helper functions'''
    def __init__(
        self,
        sequence_diagram: PlantUMLSequenceDiagram,
        get_likely_caller_from_hierarchy: Callable[[str], str],
        get_cleaned_device_name: Callable[[str, Optional[str]], str]
    ):
        self.sequence_diagram = sequence_diagram
        self.get_likely_caller_from_hierarchy = get_likely_caller_from_hierarchy
        self.get_cleaned_device_name = get_cleaned_device_name

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
            cleaned_from_device = self.get_cleaned_device_name(from_device)

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

    def handle_debug_patch_log(self, cleaned_device: str, message: str):
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
            if self.use_new_pages and likely_caller == self.actor:
                # We don't want a new page on the very first command
                if not self.brand_new_diagram:
                    self.sequence_diagram.add_new_page(command_name)
                
                self.brand_new_diagram = False

            # Create a divider if a new notebook command was run
            if self.include_dividers and likely_caller == self.actor:
                self.sequence_diagram.add_divider(command_name)


            # Add an arrow to the sequence diagram from the likely caller to the target device
            self.sequence_diagram.add_command_call(
                likely_caller, cleaned_device, f'""{target_class}.{command_name}""'
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
            message = message.replace(non_standard_subarray_device_in_log, standardised_subarray_device)

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

    def info_patch_cb(self, prefix, iso_date_string, log_level, runner,
                        action, log_line, device, message):
        if "->" in message:
            match = INCOMING_COMMAND_CALL_REGEX_PATTERN.search(message)
            if match:
                method = match.group(1)
                method = method.split(".")[1]

                # Reduce "TrackLoadTable" commands from the diagram
                if method == "TrackLoadTable":
                    self.track_load_table_count += 1
                    if self.limit_track_load_table_calls and \
                        self.track_load_table_count > TRACK_LOAD_TABLE_LIMIT:
                        return

                caller = self.get_likely_caller_from_hierarchy(device)
                self.sequence_diagram.add_command_call(caller, device, f'""{method}""')

        elif "<-" in message:
            match = RETURN_COMMAND_CALL_REGEX_PATTERN.search(message)
            if match:
                return_val = match.group(1)
                method = match.group(2)
                method = method.split(".")[1]

                # Reduce "TrackLoadTable" commands from the diagram
                if method == 'TrackLoadTable':
                    self.track_load_table_count += 1
                    if self.limit_track_load_table_calls and \
                        self.track_load_table_count > TRACK_LOAD_TABLE_LIMIT:
                        return
                    
                # The ResultCode.QUEUED logs seem to be delayed and duplicated so exclude them
                if 'ResultCode.QUEUED' in return_val:
                    return

                caller = self.get_likely_caller_from_hierarchy(device)

                self.sequence_diagram.add_command_response(
                    device, caller, f'""{method}"" -> {return_val}'
                )

    def component_state_update_cb(self, prefix, iso_date_string, log_level,
                                    runner, action, log_line, device, message):
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

    def generic_command_match_handling(self, match: Match[str], cleaned_device: str, target_device_type: str='none'):
        '''Handle a generic command with target device and add it to the sequence diagram'''
        command_name = match.group(1).strip()
        target_device = match.group(2).strip()

        # Clean the target device name for PlantUML
        cleaned_target_device = self.get_cleaned_device_name(target_device, target_device_type)

        # Add an arrow to the sequence diagram
        self.sequence_diagram.add_command_call(
            cleaned_device, cleaned_target_device, f'""{command_name}""'
        )
