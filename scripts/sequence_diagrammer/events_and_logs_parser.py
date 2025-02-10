import os
import re
import sys
from typing import Match

# Local imports
from log_parse_helper import LogParserHelper
from plantuml_helper import PlantUMLSequenceDiagram

# Submodule imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory of the script
SUBMODULE_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../.jupyter-notebooks/src"))
sys.path.append(SUBMODULE_PATH)

from notebook_tools.sequence_diagram_setup import *

class LogParser:
    def __init__(self):
        self.log_pattern_callbacks: list[tuple[str, callable]] = []

    def _parse_log_line(self, log_line):
        for pattern, pattern_cb in self.log_pattern_callbacks:
            match = re.search(pattern, log_line)
            if match:
                # prefix|iso_date_string|log_level|runner|action|log_line|device|message
                group_values = match.groups()
                pattern_cb(*group_values)
                break

    def parse_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            logs = file.readlines()

        for log in logs:
            self._parse_log_line(log)


class EventsAndLogsFileParser(LogParser):
    def __init__(
            self,
            device_hierarchy: list=[],
            limit_track_load_table_calls: bool=True,
            show_events: bool=False,
            show_component_state_updates: bool=False,
            include_dividers: bool=True,
            use_new_pages: bool=True,
            group_devices: bool=True,
            include_lrc_ids: bool=False,
            ):
        super().__init__()

        self.limit_track_load_table_calls = limit_track_load_table_calls
        self.show_events = show_events
        self.show_component_state_updates = show_component_state_updates
        self.include_dividers = include_dividers
        self.use_new_pages = use_new_pages
        self.group_devices = group_devices
        self.include_lrc_ids = include_lrc_ids

        self.sequence_diagram = PlantUMLSequenceDiagram()
        self.log_parse_helper = LogParserHelper(
            self.sequence_diagram,
            self.get_likely_caller_from_hierarchy,
            self.get_cleaned_device_name
        )

        self.device_hierarchy = device_hierarchy
        self.running_lrc_status_updates = {}

        self.log_pattern_callbacks = [
            [LOG_REGEX_PATTERN, self.log_callback],
            [EVENT_REGEX_PATTERN, self.event_callback],
        ]

        self.track_load_table_count = 0
        self.brand_new_diagram = True

    def get_likely_caller_from_hierarchy(self, device) -> str:
        for hierarchy_list in self.device_hierarchy:
            if device not in hierarchy_list or device == hierarchy_list[0]:
                continue
            device_index = hierarchy_list.index(device)
            hierarchy_index = self.device_hierarchy.index(hierarchy_list)
            likely_caller = self.device_hierarchy[hierarchy_index][device_index - 1]
            # print(f'Likely caller of device {device} is {likely_caller}')
            return likely_caller
        print(f"Setting unknown caller for device {device}")
        return "unknown"

    def get_method_from_lrc_id(self, lrc_id: str) -> str:
        return "_".join(lrc_id.split("_")[2:])

    def parse(self, file_path: str, output_file_path: str, actor: str=None):
        log_file_name = file_path.split("/")[-1]

        cleaned_log_file_name = self.sequence_diagram.clean_text(log_file_name)
        title = f"Sequence diagram generated from\n{cleaned_log_file_name}".encode(
            "unicode_escape"
        ).decode("utf-8")
        
        if not actor:
            actor = self.device_hierarchy[0][0]

        self.actor = actor

        self.running_lrc_status_updates = {}
        self.sequence_diagram.start_diagram(title, actor)

        # Add participants to ensure order of swimlanes
        previous_group, previous_colour = self.determine_box_name_and_colour(self.device_hierarchy[0][1])
        if self.group_devices:
            self.sequence_diagram.add_box(previous_group, previous_colour)

        for hierarchy_list in self.device_hierarchy:
            for device in hierarchy_list[1:]:
                current_group, current_colour = self.determine_box_name_and_colour(device)
                if self.group_devices and previous_group != current_group:
                    self.sequence_diagram.end_box()
                    self.sequence_diagram.add_box(current_group, current_colour)
                    previous_group = current_group

                self.sequence_diagram.add_participant(device)
        
        if self.group_devices:
            self.sequence_diagram.end_box()

        self.parse_file(file_path)

        self.sequence_diagram.end_diagram()

        # Save the PlantUML diagram code to a file
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(self.sequence_diagram.diagram_code)

    def get_cleaned_device_name(self, device: str, info_type: str = 'none') -> str:
        if 'full_trl' in info_type:
            # tango://tango-databaseds.staging-dish-lmc-ska001.svc.miditf.internal.skao.int:10000/mid-dish/dish-manager/SKA001
            device = device.split('/', maxsplit=3)[-1] # only get the trl part of the full name

        try:
            cleaned_device = device.split('/', maxsplit=1)[1]  # e.g. dish-manager/ska001
        except Exception as e:
            print(f'Error when cleaning device ({device}): {e}')
            return ''
            

        # mid-csp and mid-sdp are both just called "subarray" or "control", to differentiate, add the 
        # first part of the trl. The spfrxpu devices also need the first element to get the dish number
        if cleaned_device.startswith('subarray/') \
            or cleaned_device.startswith('spfrxpu/') \
            or cleaned_device.startswith('control/'):
            if 'event' in info_type:
                # e.g. MidCspSubarray(mid-csp/subarray/01)
                trl_start = device.split('(', 1)[1]
            elif 'log' in info_type:
                # e.g. tango-device:mid-csp/subarray/01
                trl_start = device.split('tango-device:', 1)[1]
            else:
                # e.g. mid-csp/subarray/01 or [ska001/spfrxpu/controller]
                trl_start = device.strip('[')

            cleaned_device = f'{trl_start.split("/")[0]}/{cleaned_device}'

        # Remove last character if it's an event because the closing parenthesis will still be there
        cleaned_device = cleaned_device[:-1] if info_type == 'event' or device.startswith('[') else cleaned_device

        # Replace / with . and for plantUML
        cleaned_device = cleaned_device.replace('/', '.')

        return cleaned_device.lower()

    def determine_box_name_and_colour(self, device: str) -> tuple[str, str]:
        '''Determine the group the device falls under and assign the appropriate colour'''
        match device:
            case _ if device.startswith('tm'):
                return DeviceGroup.TMC.value
            case _ if device.startswith(('mid-csp', 'mid_csp', 'sub_elt')):
                return DeviceGroup.CSP.value
            case _ if device.startswith('mid-sdp'):
                return DeviceGroup.SDP.value
            case _ if device.startswith(('dish-', 'ds-', 'ska', 'simulator_spfc')):
                return DeviceGroup.DISHES.value
            case _:
                print(f'Device {device} set to UNKNOWN group')
                return DeviceGroup.UNKNOWN.value

    def log_callback(self, prefix: str, iso_date_string: str, log_level: str,
                     runner: str, action: str, log_line: str, device: str, message: str):
        # Ignore empty devices        
        if device == "":
            return
        
        # Example log message:
        # 1724676115.079 -  Log  - 1|2024-08-26T12:41:55.079Z|DEBUG|Thread-9 (_event_consumer)|
        # _component_state_changed|dish_manager_cm.py#390|tango-device:mid-dish/dish-manager/SKA001|...
        cleaned_device = self.get_cleaned_device_name(device, 'log')

        if action in ['update_long_running_command_result', 'update_command_result']:
            # <prefix>|<date>|INFO|longRunningCommandResult|update_long_running_command_result|<log_line>|
            # tango-device:ska_mid/tm_subarray_node/1|Received longRunningCommandResult event for device:
            #  ska_mid/tm_leaf_node/sdp_subarray01, with value: ('1731055110.2204533_15076717473253_On', '[0, "Command Completed"]')
            self.log_parse_helper.handle_lrc_result_log(cleaned_device, message)

        elif action in ['invoke_command', 'execute_command']:
            # <prefix>|<date>|DEBUG|<runner>|invoke_command|<log_line>|tango-device:ska_mid/tm_central/central_node|
            # Invoked On on device ska_mid/tm_subarray_node/2
            self.log_parse_helper.handle_invoke_or_execute_command_log(cleaned_device, message)

        elif action == '_debug_patch':
            # <prefix>|<date>|DEBUG|<runner|_debug_patch|<log_line>|tango-device:ska_mid/tm_central/central_node|
            # -> CentralNodeMid.TelescopeOn()
            self.log_parse_helper.handle_debug_patch_log(cleaned_device, message)

        elif action == '_set_k_numbers_to_dish':
            # <prefix>|<date>|INFO|<runner>|_set_k_numbers_to_dish|<log_line>|
            # tango-device:ska_mid/tm_central/central_node|Invoking SetKValue on dish adapter ska_mid/tm_leaf_node/d0001
            self.log_parse_helper.handle_set_k_numbers_to_dish_log(cleaned_device, message)
        
        elif action in ['turn_on_csp', 'turn_on_sdp', 'turn_off_csp', 'turn_off_sdp']:
            # <prefix>|<date>|INFO|<runner>|turn_on_csp|<log_line>|tango-device:ska_mid/tm_central/central_node|
            # Invoking On command for ska_mid/tm_leaf_node/csp_master devices
            self.log_parse_helper.handle_csp_sdp_invoking_on_off_command_log(cleaned_device, message)

        elif action in [
            'do_mid',
            'call_adapter_method', 
            'assign_csp_resources',
            'scan_dishes',
        ]:
            # <prefix>|<date>|INFO|<runner>|assign_csp_resources|<log_line>|
            # tango-device:ska_mid/tm_subarray_node/1|AssignResources command invoked on ska_mid/tm_leaf_node/csp_subarray01
            # <prefix>|<date>|INFO|<runner>|do_mid|<log_line>|tango-device:ska_mid/tm_leaf_node/csp_subarray01|
            # Invoking AssignResources command on mid-csp/subarray/01
            self.log_parse_helper.handle_invoking_most_commands_log(cleaned_device, message)

        elif action in ['release_csp_resources', 'release_sdp_resources']:
            # These guys wanted to be special for release resources
            # <prefix>|<date>|INFO|<runner>|release_sdp_resources|<log_line>|tango-device:ska_mid/tm_subarray_node/1|
            # ReleaseAllResources command invoked on SDP Subarray Leaf Node  ska_mid/tm_leaf_node/sdp_subarray01
            self.log_parse_helper.handle_csp_sdp_release_resources_command_log(cleaned_device, message)

        elif action == "_info_patch":
            self.log_parse_helper.info_patch_cb(
                prefix, iso_date_string, log_level, runner, action, log_line, cleaned_device, message
            )
        elif action == "_update_component_state" and self.show_component_state_updates:
            self.log_parse_helper.component_state_update_cb(
                prefix, iso_date_string, log_level, runner, action, log_line, cleaned_device, message
            )

    def event_callback(self, prefix, device: str, event_attr, val):
        # Ignore empty devices        
        if device == "":
            return

        # Example event messages:
        # 1724660914.761 - Event - 2024-08-26 08:28:34.761448	DishManager(mid-dish/dish-manager/ska001)
        # 	longrunningcommandstatus	('1724660914.663982_241979260268973_SetStowMode', 'COMPLETED')
        # 1724660914.761 - Event - 2024-09-18 08:44:43.859312	MidCspSubarray(mid-csp/subarray/01)
        #   longrunningcommandstatus	('1726641882.6817706_174896405886953_AssignResources', 'STAGING')
        cleaned_device = self.get_cleaned_device_name(device, "event")
        caller = self.get_likely_caller_from_hierarchy(cleaned_device)

        if "longrunningcommand" in event_attr:
            self.handle_lrc_event_log(cleaned_device, caller, event_attr, val)
        elif self.show_events:
            self.sequence_diagram.add_note_over(
                cleaned_device,
                f'Event\n""{event_attr} = {val.strip()}""'.encode("unicode_escape").decode(
                    "utf-8"
                ),
            )

    def handle_lrc_event_log(self, device, caller, event_attr, val):
        if "longrunningcommandstatus" in event_attr:
            lrc_statuses = LRC_TUPLE_REGEX_PATTERN.findall(val)
            for index, (lrc_id, status) in enumerate(lrc_statuses):
                # If there are any newer updates for this lrc in the LRC statuses then skip this
                newer_status_found = False
                if index + 1 < len(lrc_statuses):
                    for i in range(index + 1, len(lrc_statuses)):
                        if lrc_statuses[i][0] == lrc_id:
                            newer_status_found = True
                            break

                if newer_status_found:
                    break

                method_name = self.get_method_from_lrc_id(lrc_id)

                if status == "STAGING":
                    # Only track methods which are called in the scope of the file
                    # This avoids some noise left over in LRC attributes from previous test / setup
                    self.running_lrc_status_updates[lrc_id] = []

                # Only update if its a method called in the scope of this file and its a new status
                if (
                    lrc_id in self.running_lrc_status_updates
                    and status not in self.running_lrc_status_updates[lrc_id]
                    and status != "STAGING"
                ):
                    self.running_lrc_status_updates[lrc_id].append(status)
                    self.sequence_diagram.add_command_response(
                        device, caller, f'""{lrc_id if self.include_lrc_ids else method_name}"" -> {status}'
                    )
        elif "longrunningcommandprogress" in event_attr:
            lrc_progresses = LRC_TUPLE_REGEX_PATTERN.findall(val)
            for lrc_id, progress in lrc_progresses:
                # Only show progress updates for methods which have been staged
                if lrc_id in self.running_lrc_status_updates:
                    method_name = self.get_method_from_lrc_id(lrc_id)
                    self.sequence_diagram.add_command_call(
                        device, device, f'""{lrc_id if self.include_lrc_ids else method_name}"" -> {progress}'
                    )
        elif event_attr == "longrunningcommandresult":
            pass
