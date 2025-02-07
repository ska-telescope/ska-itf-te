import tango
from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass
class TrackedDevice:
    """Class to group tracked device information"""

    device_proxy: tango.DeviceProxy
    attribute_names: Tuple[str]
    subscription_ids: List[int] = field(default_factory=list)

class EventPrinter:
    """Class that writes attribute changes to a file"""

    def __init__(self, filename: str, tracked_devices: Tuple[TrackedDevice] = ()) -> None:
        self.tracked_devices = tracked_devices
        self.filename = filename
        self.events = []

    def __enter__(self):
        for tracked_device in self.tracked_devices:
            dp = tracked_device.device_proxy
            for attr_name in tracked_device.attribute_names:
                sub_id = dp.subscribe_event(attr_name, tango.EventType.CHANGE_EVENT, self)
                tracked_device.subscription_ids.append(sub_id)

    def __exit__(self, exc_type, exc_value, exc_tb):
        for tracked_device in self.tracked_devices:
            try:
                dp = tracked_device.device_proxy
                for sub_id in tracked_device.subscription_ids:
                    dp.unsubscribe_event(sub_id)
            except tango.DevError:
                pass

    def add_event(self, timestamp, message):
        self.events.append((timestamp, message))
        with open(self.filename, "a") as open_file:
            open_file.write("\n" + message)

    def push_event(self, ev: tango.EventData):
        event_string = ""
        if ev.err:
            err = ev.errors[0]
            event_string = f"\nEvent Error {err.desc} {err.origin} {err.reason}"
        else:
            attr_name = ev.attr_name.split("/")[-1]
            attr_value = ev.attr_value.value
            if ev.attr_value.type == tango.CmdArgType.DevEnum:
                attr_value = ev.device.get_attribute_config(attr_name).enum_labels[attr_value]

            event_string = f"Event - {ev.reception_date}\t{ev.device}\t{attr_name}\t{attr_value}"

        self.add_event(ev.reception_date.totime(), event_string)
