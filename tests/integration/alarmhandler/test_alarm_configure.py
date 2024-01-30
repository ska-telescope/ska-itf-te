"""load and acknowledge the configured alarms."""
import pytest
from tango import DeviceProxy


@pytest.mark.skamid
def test_load_alarm():
    """Configure alarms on alarm handler instance."""
    alarm_handler = DeviceProxy("alarm/handler/01")
    alarm_formula = (
        "tag=centralnode_telescopehealthstate_unknown;formula="
        "(ska_mid/tm_central/central_node/telescopehealthState == 13);"
        "priority=log;group=none;message="
        '("alarm for central node telescopehealthstate unknown")'
    )
    alarm_handler.Load(alarm_formula)
    alarm_list = alarm_handler.alarmList
    assert alarm_list == ("centralnode_telescopehealthstate_unknown",)
    alarm_handler.Ack("centralnode_telescopehealthstate_unknown")
    tear_down(alarm_handler, alarm_list)


def tear_down(alarm_handler_device: DeviceProxy, alarms_to_remove: list):
    """Remove configured alarms using the tag.

    :param alarm_handler_device: device proxy for alarm handler device
    :param alarms_to_remove: list of alarms to remove
    """
    for tag in alarms_to_remove:
        alarm_handler_device.Remove(tag)
    assert alarm_handler_device.alarmList == ()
