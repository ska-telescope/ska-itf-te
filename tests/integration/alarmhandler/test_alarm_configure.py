"""Configure Alarm Tests"""
import logging

import pytest
from tango import DeviceProxy

logger = logging.getLogger(__name__)


@pytest.mark.skamid
def test_load_alarm():
    """A method to load tmc alarm for Alarm handler instance"""
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
    tear_down_configured_alarms(alarm_handler, alarm_list)


def tear_down_configured_alarms(
    alarm_handler_device: DeviceProxy, alarms_to_remove: list
):
    """
    A method to remove configured alarms using the tag
    Arg:
        alarm_handler_device(DeviceProxy): device proxy for
        alarm handler device
        alarms_to_remove(list): list of alarms to remove
    """
    for tag in alarms_to_remove:
        alarm_handler_device.Remove(tag)
    assert alarm_handler_device.alarmList == ()
