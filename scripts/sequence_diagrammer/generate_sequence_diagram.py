import os
import sys
import tango
from datetime import datetime, timezone

# Local imports
from scripts.sequence_diagrammer.event_printer import EventPrinter, TrackedDevice
from scripts.sequence_diagrammer.events_and_logs_parser import EventsAndLogsFileParser
from scripts.sequence_diagrammer.log_retriever import LogRetriever

# Submodule imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory of the script
SUBMODULE_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../.jupyter-notebooks/src"))
sys.path.append(SUBMODULE_PATH)

from ska_mid_jupyter_notebooks.helpers.configuration import get_dish_namespace
from notebook_tools.sequence_diagram_setup import *


class sequenceDiagrammer:
    """Class for starting event listing and generating sequence diagrams."""

    def __init__(self, sut_namespace: str = ''):
        """:param sut_namespace: _description_."""

        os.environ["TZ"] = "Africa/Johannesburg"

        # Set up namespaces and pods
        if sut_namespace:
            self.sut_namespace = sut_namespace 
        elif os.getenv("KUBE_NAMESPACE"):
            self.sut_namespace = os.getenv("KUBE_NAMESPACE")
        else:
            self.sut_namespace = 'staging'  # default to staging

        if "DISH_IDS" in os.environ:
            dish_ids: str = os.environ["DISH_IDS"]
        else:
            dish_ids = "SKA001 SKA036 SKA063 SKA100"  # conform to how they're saved in the env var

        # Convert string of space-separated IDs to a list of indexes
        self.dish_indexes = [str(dish_id[-3:]) for dish_id in list(dish_ids.split(" "))]

        self.dish_namespaces: list[str] = [get_dish_namespace(
            self.sut_namespace, f'SKA{index}'
        ) for index in self.dish_indexes]

        self.namespaces_pods: dict[str, list[str]] = define_pods_for_logs(
            self.dish_indexes, self.sut_namespace, self.dish_namespaces
        )

        # Setup tracked devices
        self.tracked_device_trls: list[str] = define_tracked_device_trls(self.dish_indexes, self.sut_namespace, self.dish_namespaces)
        self.tracked_devices = [
            TrackedDevice(
                tango.DeviceProxy(device_trl),
                (
                    "longrunningcommandstatus",
                    "longrunningcommandresult",
                    "longrunningcommandprogress",
                ),
            )
            for device_trl in self.tracked_device_trls
        ]
        # Configure device hierarchy
        self.device_hierarchy: list[list[str]] = setup_device_hierarchy(self.dish_indexes)

        # Get the current datetime
        datetime_start = datetime.now(timezone.utc) 
        self.iso_start = datetime_start.isoformat()

        date = datetime_start.strftime("%Y%m%d")
        time_start = datetime_start.strftime("%H%M%S")

        self.events_file_name = f"generated_events-{date}-{time_start}.txt"
        self.events_and_logs_file_name = f"events_and_logs-{date}-{time_start}.txt"
        self.sequence_diagram_file_name = f"sequence-diagram.puml"

        self.event_printer = EventPrinter(
            self.events_file_name, self.tracked_devices
        )

        self.log_retriever = LogRetriever()

        # To generate a more verbose diagram with events and component state updates,
        # set 2nd and 3rd arguments to True
        self.file_parser = EventsAndLogsFileParser(
            device_hierarchy=self.device_hierarchy,
        )

    def start_tracking_events(self):
        """."""
        self.event_printer.start()

    def stop_tracking_and_generate_diagram(self):
        """."""
        self.event_printer.stop()

        # Loop over each namespace and its pods
        # * Note: This takes a handful of seconds
        all_pod_logs = {}
        for namespace, pods in self.namespaces_pods.items():
            for pod in pods:
                all_pod_logs[pod] = self.log_retriever.get_pod_logs_and_timestamps(
                    namespace, pod, self.iso_start
                )

        # Combine and sort logs/events
        captured_events = self.event_printer.events
        combined_events_and_logs = []

        for logs in all_pod_logs.values():
            combined_events_and_logs.extend(logs)

        combined_events_and_logs.extend(captured_events)

        combined_events_and_logs.sort(key=lambda x: x[0])

        # print(combined_events_and_logs)

        # Write the combined entries to the output file
        with open(self.events_and_logs_file_name, "w") as file:
            for timestamp, message in combined_events_and_logs:
                file.write(f"{timestamp:.3f} - {message}\n")

        # Parse events and logs file into puml
        events_and_logs_file_path = f"./{self.events_and_logs_file_name}"

        self.file_parser.parse(
            events_and_logs_file_path, self.sequence_diagram_file_name
        )
