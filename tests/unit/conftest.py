"""Test this thing."""
import os
import pytest
import tango


@pytest.fixture()
def tango_devices() -> list:
    """
    Read Tango device names from database.

    :return: list of names
    """
    tango_devices: list = []
    # Connect to database
    try:
        database = tango.Database()
    except Exception:
        tango_host = os.getenv("TANGO_HOST")
        print("[FAILED] Could not connect to Tango database %s", tango_host)
    # Read devices
    device_list = database.get_device_exported("*")
    print(f"[  OK  ] {len(device_list)} devices available")

    for device in sorted(device_list.value_string):
        if device[0:3] == "sys" or device[0:7] == "dserver":
            continue
        tango_devices.append(device)

    return tango_devices
