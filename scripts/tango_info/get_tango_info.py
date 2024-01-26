#!/usr/bin/python
"""
Read information from Tango database.
"""
import getopt
import logging
import os
import sys
import time
from typing import Any, Tuple

import tango
from ska_control_model import AdminMode

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger(__name__)
_module_logger.setLevel(logging.WARNING)

KUBE_NAMESPACE = "ci-ska-mid-itf-at-1820-tmc-test-sdp-notebook-v2"
CLUSTER_DOMAIN = "miditf.internal.skao.int"
DATABASEDS_NAME = "tango-databaseds"


def connect_device(device: str) -> Tuple[Any, int]:
    """
    Display Tango device in mark-down format

    :param device: device name
    """
    # Connect to device proxy
    dev = tango.DeviceProxy(device)
    # Read state
    try:
        dev_state = dev.State()
    except Exception:
        dev_state = None
    return dev, dev_state


def check_device(dev: tango.DeviceProxy) -> bool:
    try:
        dev.ping()
        return True
    except Exception:
        return False


def device_state(dev: tango.DeviceProxy) -> None:
    """
    Display status information for Tango device.

    :param dev: Tango device handle
    :return: None
    """
    dev_name = dev.name()
    print(f"Device {dev_name}")
    print(f"\tAdmin mode                     : {dev.adminMode}")
    print(f"\tDevice status                  : {dev.Status()}")
    print(f"\tDevice state                   : {dev.State()}")
    try:
        print(f"\tObservation state              : {repr(dev.obsState)}")
        show_obs_state(dev.obsState)
    except AttributeError:
        _module_logger.info("Device %s does not have an observation state", dev_name)
    print(f"versionId                        : {dev.versionId}")
    print(f"build State                      : {dev.buildState}")
    print(f"logging level                    : {dev.loggingLevel}")
    print(f"logging Targets                  : {dev.loggingTargets}")
    print(f"health State                     : {dev.healthState}")
    print(f"control Mode                     : {dev.controlMode}")
    print(f"simulation Mode                  : {dev.simulationMode}")
    print(f"test Mode                        : {dev.testMode}")
    print(f"long Running Commands In Queue   : {dev.longRunningCommandsInQueue}")
    print(f"long Running Command IDs InQueue : {dev.longRunningCommandIDsInQueue}")
    print(f"long Running Command Status      : {dev.longRunningCommandStatus}")
    print(f"long Running Command Progress    : {dev.longRunningCommandProgress}")
    print(f"long Running Command Result      : {dev.longRunningCommandResult}")


def setup_device(dev_name: str) -> Tuple[int, tango.DeviceProxy]:
    """
    Set up device connection and timeouts.

    :param dev_name: Tango device name
    :return: error condition and Tango device handle
    """
    print("*** Setup Device connection and Timeouts ***")
    print(f"Tango device : {dev_name}")
    dev = tango.DeviceProxy(dev_name)
    # check AdminMode
    csp_admin = get_tango_admin(dev)
    if csp_admin:
        # Set Adminmode to OFFLINE and check state
        csp_admin = set_tango_admin(dev, False)
        if csp_admin:
            _module_logger.error("Could not turn off admin mode")
            return 1, None
    return 0, dev


def get_tango_admin(dev: tango.DeviceProxy) -> bool:
    """
    Read admin mode for a Tango device.

    :param dev: Tango device handle
    :return: True when device is in admin mode
    """
    csp_admin = dev.adminMode
    if csp_admin == AdminMode.ONLINE:
        print("Device admin mode online")
        return False
    if csp_admin == AdminMode.OFFLINE:
        print("Device admin mode offline")
    else:
        print(f"Device admin mode {csp_admin}")
    return True


def set_tango_admin(dev: Any, dev_adm: bool, sleeptime: int = 2) -> bool:
    """
    Write admin mode for a Tango device.

    :param dev: Tango device
    :param dev_adm: admin mode flag
    :param sleeptime: seconds to sleep
    :return: True when device is in admin mode
    """
    print(f"*** Set Adminmode to {dev_adm} and check state ***")
    if dev_adm:
        dev.adminMode = 1
    else:
        dev.adminMode = 0
    time.sleep(sleeptime)
    return get_tango_admin(dev)


def show_device_state(device: str) -> int:
    """
    Display Tango device name only

    :param device: device name
    """
    _dev, dev_state = connect_device(device)
    # pylint: disable-next=c-extension-no-member
    if dev_state != tango._tango.DevState.ON:
        print(f"  {device}")
        return 0
    print(f"* {device}")
    return 1


def show_device(device: str, fforce: bool) -> int:  # noqa: C901
    """
    Display Tango device in text format

    :param device: device name
    :param fforce: get commands and attributes regadrless of state
    """
    dev, dev_state = connect_device(device)
    # pylint: disable-next=c-extension-no-member
    if dev_state != tango._tango.DevState.ON:
        print(f"  {device}", end="")
        if not fforce:
            print()
            return 0
    else:
        print(f"* {device}", end="")
    try:
        cmds = sorted(dev.get_command_list())
    except Exception:
        cmds = []
    print(f" : {len(cmds)} \033[3mcommands\033[0m,", end="")
    try:
        attribs = sorted(dev.get_attribute_list())
    except Exception:
        attribs = []
    print(f" {len(attribs)} \033[1mattributes\033[0m")
    dev_info = dev.info()
    print(f"Description  : {dev.description()}")
    print(f"Device class : {dev_info.dev_class}")
    print(f"Server host  : {dev_info.server_host}")
    print(f"Server ID    : {dev_info.server_id}")
    try:
        print(f"Resources    : {dev.assignedresources}")
    except tango.DevFailed:
        print(f"Resources    : could not be read")
    except AttributeError:
        pass
    try:
        print(f"VCC state    : {dev.assignedVccState}")
    except AttributeError:
        pass
    try:
        dev_obs = dev.obsState
        print(f"Observation  : {get_obs_state(dev_obs)}")
    except Exception:
        pass
    # Print commands in italic
    for cmd in cmds:
        print(f"\t\033[3m{cmd}\033[0m")
    # Print attributes in bold
    for attrib in attribs:
        print(f"\t\033[1m{attrib}\033[0m : ", end="")
        try:
            print(f"{dev.read_attribute(attrib).value}")
        except Exception:
            print("could not be read")
    if cmds or attribs:
        return 1
    return 0


def show_device_markdown(device: str) -> int:  # noqa: C901
    """
    Display Tango device in mark-down format

    :param device: device name
    """
    rval = 0
    print(f"## Device *{device}*")
    # Connect to device proxy
    dev = tango.DeviceProxy(device)
    # Read database host
    print(f"### Database host\n{dev.get_db_host()}")
    dev, dev_state = connect_device(device)
    if dev_state is not None:
        print(f"### State\n{dev_state}")
    else:
        print("### State\nNONE")
    # Read information
    try:
        print(f"### Information\n```\n{dev.info()}\n```")
    except Exception:
        print("### Information\n```\nNONE\n```")
    # Read commands
    try:
        cmds = sorted(dev.get_command_list())
        # Display version information
        if "GetVersionInfo" in cmds:
            verinfo = dev.GetVersionInfo()
            print(f"### Version\n```\n{verinfo[0]}\n```")
        # Display commands
        print("### Commands")
        print("```\n%s\n```" % "\n".join(cmds))
        # Read command configuration
        cmd_cfgs = dev.get_command_config()
        for cmd_cfg in cmd_cfgs:
            print(f"#### Command *{cmd_cfg.cmd_name}*")
            # print(f"```\n{cmd_cfg}\n```")
            print("|Name |Value |")
            print("|:----|:-----|")
            if cmd_cfg.cmd_tag != 0:
                print(f"|cmd_tag|{cmd_cfg.cmd_tag}|")
            print(f"|disp_level|{cmd_cfg.disp_level}|")
            print(f"|in_type|{cmd_cfg.in_type}|")
            if cmd_cfg.in_type_desc != "Uninitialised":
                print(f"|in_type|{cmd_cfg.in_type_desc}")
            print(f"|out_type|{cmd_cfg.out_type}|")
            if cmd_cfg.out_type_desc != "Uninitialised":
                print(f"|in_type|{cmd_cfg.out_type_desc}")
    except Exception:
        cmds = []
        print("### Commands\n```\nNONE\n```")
    # Read status
    if "Status" in cmds:
        print(f"#### Status\n{dev.Status()}")
    else:
        print("#### Status\nNo Status command")
    # Read attributes
    print("### Attributes")
    # pylint: disable-next=c-extension-no-member
    if dev_state == tango._tango.DevState.ON:
        rval = 1
        attribs = sorted(dev.get_attribute_list())
        print("```\n%s\n```" % "\n".join(attribs))
        for attrib in attribs:
            print(f"#### Attribute *{attrib}*")
            try:
                print(f"##### Value\n```\n{dev.read_attribute(attrib).value}\n```")
            except Exception:
                print(f"```\n{attrib} could not be read\n```")
            try:
                attrib_cfg = dev.get_attribute_config(attrib)
                print(f"##### Description\n```\n{attrib_cfg.description}\n```")
                # print(f"##### Configuration\n```\n{attrib_cfg}\n```")
            except Exception:
                print(f"```\n{attrib} configuration could not be read\n```")
    else:
        print("```\nNot reading attributes in offline state\n```")
    print("")
    return rval


def show_devices(evrythng: int, fforce: bool, itype: str | None) -> None:  # noqa: C901
    """
    Display information about Tango devices

    :param evrythng: flag for markdown output
    :param fforce: get commands and attributes regadrless of state
    :param itype: filter device name
    """

    # Get Tango database hist
    tango_host = os.getenv("TANGO_HOST")
    _module_logger.info("Tango host %s" % tango_host)

    # Connect to database
    try:
        database = tango.Database()
    except Exception:
        _module_logger.error("Could not connect to Tango database %s", tango_host)
        return
    # Read devices
    device_list = database.get_device_exported("*")
    _module_logger.info(f"{len(device_list)} devices available")

    _module_logger.info("Read %d devices" % (len(device_list)))
    if evrythng == 2:
        print("# Tango devices")
        print("## Tango host\n```\n%s\n```" % tango_host)
        print(f"## Number of devices\n{len(device_list)}")
    dev_count = 0
    on_dev_count = 0
    for device in sorted(device_list.value_string):
        # ignore sys devices
        if device[0:4] == "sys/":
            _module_logger.info(f"Skip {device}")
            continue
        # Check device name against mask
        if itype:
            iupp = device.upper()
            if itype not in iupp:
                _module_logger.info(f"Ignore {device}")
                continue
        dev_count += 1
        if evrythng == 2:
            on_dev_count += show_device_markdown(device)
        elif evrythng == 1:
            on_dev_count += show_device(device, fforce)
        else:
            on_dev_count += show_device_state(device)

    if evrythng == 2:
        if itype:
            print("## Summary")
            print(f"Found {dev_count} devices matching {itype}")
        else:
            print("## Summary")
            print(f"Found {dev_count} devices")
        print(f"There are {on_dev_count} active devices")
        print("# Kubernetes pod\n>", end="")


def check_command(dev: Any, c_name: str | None) -> bool:
    try:
        cmds = sorted(dev.get_command_list())
    except Exception:
        cmds = []
    if c_name in cmds:
        return True
    return False


def show_attributes(evrythng: int, fforce: bool, a_name: str | None) -> None:
    """
    Display information about Tango devices

    :param evrythng: flag for markdown output
    :param fforce: get commands and attributes regadrless of state
    :param a_name: filter attribute name
    """

    # Get Tango database hist
    tango_host = os.getenv("TANGO_HOST")
    _module_logger.info("Tango host %s" % tango_host)

    # Connect to database
    try:
        database = tango.Database()
    except Exception:
        _module_logger.error("Could not connect to Tango database %s", tango_host)
        return
    # Read devices
    device_list = database.get_device_exported("*")
    _module_logger.info(f"{len(device_list)} devices available")

    _module_logger.info("Read %d devices" % (len(device_list)))
    if evrythng == 2:
        print("# Tango devices")
        print("## Tango host\n```\n%s\n```" % tango_host)
        print(f"## Number of devices\n{len(device_list)}")

    for device in sorted(device_list.value_string):
        # ignore sys devices
        if device[0:4] == "sys/":
            _module_logger.info(f"Skip {device}")
            continue
        dev, _dev_state = connect_device(device)
        try:
            attribs = sorted(dev.get_attribute_list())
        except Exception:
            attribs = []
        if a_name in attribs:
            print(f"* {device}", end="")
            print(f"\t\033[1m{a_name}\033[0m")


def show_commands(evrythng: int, fforce: bool, c_name: str | None) -> None:
    """
    Display information about Tango devices

    :param evrythng: flag for markdown output
    :param fforce: get commands and attributes regadrless of state
    :param c_name: filter command name
    """

    # Get Tango database hist
    tango_host = os.getenv("TANGO_HOST")
    _module_logger.info("Tango host %s" % tango_host)

    # Connect to database
    try:
        database = tango.Database()
    except Exception:
        _module_logger.error("Could not connect to Tango database %s", tango_host)
        return
    # Read devices
    device_list = database.get_device_exported("*")
    _module_logger.info(f"{len(device_list)} devices available")

    _module_logger.info("Read %d devices" % (len(device_list)))

    for device in sorted(device_list.value_string):
        # ignore sys devices
        if device[0:4] == "sys/":
            _module_logger.info(f"Skip {device}")
            continue
        dev, _dev_state = connect_device(device)
        chk_cmd = check_command(dev, c_name)
        if chk_cmd:
            print(f"* {dev.name()}", end="")
            print(f"\t\033[1m{c_name}\033[0m")


OBSERVATION_STATES = [
    "EMPTY",
    "RESOURCING",
    "IDLE",
    "CONFIGURING",
    "READY",
    "SCANNING",
    "ABORTING",
    "ABORTED",
    "RESETTING",
    "FAULT",
    "RESTARTING",
]


def get_obs_state(obs_stat: int) -> str:
    """
    Display Python enumerated type for observing state.

    :param obs_stat: observing state numeric value
    :return: state description
    """
    return OBSERVATION_STATES[obs_stat]


def show_obs_state(obs_stat: int) -> None:  # noqa: C901
    """
    Display Python enumerated type for observing state.

    :param obs_stat: observing state numeric value
    """

    if obs_stat == 0:
        # EMPTY = 0
        print(
            """EMPTY:
        The sub-array has no resources allocated and is unconfigured.
        """
        )
    elif obs_stat == 1:
        # RESOURCING = 1
        # In normal science operations these will be the resources required
        # for the upcoming SBI execution.
        #
        # This may be a complete de/allocation, or it may be incremental. In
        # both cases it is a transient state; when the resourcing operation
        # completes, the subarray will automatically transition to EMPTY or
        # IDLE, according to whether the subarray ended up having resources or
        # not.
        #
        # For some subsystems this may be a very brief state if resourcing is
        # a quick activity.
        print(
            """RESOURCING:
        Resources are being allocated to, or deallocated from, the subarray.
        """
        )
    elif obs_stat == 2:
        # IDLE = 2
        print(
            """IDLE:
        The subarray has resources allocated but is unconfigured.
        """
        )
    elif obs_stat == 3:
        # CONFIGURING = 3
        print(
            """CONFIGURING:
        The subarray is being configured for an observation.
        This is a transient state; the subarray will automatically
        transition to READY when configuring completes normally.
        """
        )
    elif obs_stat == 4:
        # READY = 4
        print(
            """READY:
        The subarray is fully prepared to scan, but is not scanning.
        It may be tracked, but it is not moving in the observed coordinate
        system, nor is it taking data.
        """
        )
    elif obs_stat == 5:
        # SCANNING = 5
        print(
            """SCANNING:
        The subarray is scanning.
        It is taking data and, if needed, all components are synchronously
        moving in the observed coordinate system.
        Any changes to the sub-systems are happening automatically (this
        allows for a scan to cover the case where the phase centre is moved
        in a pre-defined pattern).
        """
        )
    elif obs_stat == 6:
        # ABORTING = 6
        print(
            """ABORTING:
         The subarray has been interrupted and is aborting what it was doing.
        """
        )
    elif obs_stat == 7:
        # ABORTED = 7
        print("""ABORTED: The subarray is in an aborted state.""")
    elif obs_stat == 8:
        # RESETTING = 8
        print(
            """RESETTING:
        The subarray device is resetting to a base (EMPTY or IDLE) state.
        """
        )
    elif obs_stat == 9:
        # FAULT = 9
        print(
            """FAULT:
        The subarray has detected an error in its observing state.
        """
        )
    elif obs_stat == 10:
        # RESTARTING = 10
        print(
            """RESTARTING:
        The subarray device is restarting.
        After restarting, the subarray will return to EMPTY state, with no
        allocated resources and no configuration defined.
        """
        )
    else:
        print(f"Unknown state {obs_stat}")


def show_long_running_command(dev: Any) -> int:
    """
    Display long-running command.

    :param dev: Tango device handle
    :return: error condition
    """
    rc = len(dev.longRunningCommandsInQueue)
    print(f"Long running commands on device {dev.name()} : {rc} items")
    print("\tCommand IDs In Queue :")
    for qcmd in dev.longRunningCommandIDsInQueue:
        print(f"\t\t{qcmd}")
    print("\tCommand Progress :")
    for qcmd in dev.longRunningCommandProgress:
        print(f"\t\t{qcmd}")
    print("\tCommand Result :")
    n = 0
    lstat = len(dev.longRunningCommandResult)
    while n < lstat:
        print(f"\t\t{dev.longRunningCommandResult[n]}", end="")
        print(f"\t{dev.longRunningCommandResult[n+1]}", end="")
        print()
        n += 2
    print("\tCommand Status :")
    n = 0
    lstat = len(dev.longRunningCommandStatus)
    while n < lstat:
        print(f"\t\t{dev.longRunningCommandStatus[n+1]:12}", end="")
        print(f"\t{dev.longRunningCommandStatus[n]}")
        n += 2
    print("\tCommands In Queue :")
    for qcmd in dev.longRunningCommandsInQueue:
        print(f"\t\t{qcmd}")
    return rc


def show_long_running_commands(dev_name: str) -> int:
    """
    Display long-running commands.

    :param dev_name: Tango device name
    :return: None
    """
    dev = tango.DeviceProxy(dev_name)
    show_long_running_command(dev)
    return 0


# def usage(p_name: str) -> None:
#     """
#     Show how it is done.
#
#     :param p_name: executable name
#     """
#     print("Display device names only")
#     print(f"\t{p_name}")
#     print("Display all devices")
#     print(f"\t{p_name} [-f]")
#     print(f"\t{p_name} -e [-f]")
#     print("Filter on device name")
#     print(f"\t{p_name} [-f] --device=<DEVICE>")
#     print(f"\t{p_name} -e [-f] --device=<DEVICE>")
#     print(f"\t{p_name} -q [-f] --device=<DEVICE>")
#     print("Filter on attribute name")
#     print(f"\t{p_name} -e [-f] --attribute=<ATTRIBUTE>")
#     print("where:")
#     print("\t-e\tdisplay in markdown format")
#     print("\t-q\tdisplay status and name only")
#     print("\t-f\tget commands and attributes regadrless of state")
#     print(
#         "\t--device=<DEVICE>\tdevice name, e.g. 'csp'"
#         " (not case sensitive, only a part is needed)"
#     )
#     print("--attribute=<ATTRIBUTE>\tattribute name, e.g. 'obsState'")
#
#
# def main(y_arg: list) -> int:  # noqa: C901
#     """
#     Read and display Tango devices.
#
#     :param y_arg: input arguments
#     """
#     itype: str | None = None
#     evrythng: int = 1
#     fforce: bool = False
#     show_host: bool = False
#     tgo_attrib: str | None = None
#     tgo_cmd: str | None = None
#     try:
#         opts, _args = getopt.getopt(
#             y_arg[1:],
#             "aefhqvVA:C:I:",
#             ["help", "device=", "attribute=", "command="],
#         )
#     except getopt.GetoptError as opt_err:
#         print(f"Could not read command line: {opt_err}")
#         return 1
#
#     for opt, arg in opts:
#         if opt in ("-h", "--help"):
#             usage(os.path.basename(y_arg[0]))
#             sys.exit(1)
#         elif opt in ("-A", "--attribute"):
#             tgo_attrib = arg
#         elif opt in ("-C", "--command"):
#             tgo_cmd = arg
#         elif opt in ("-I", "--device"):
#             itype = arg.upper()
#         elif opt == "-a":
#             show_host = True
#         elif opt == "-e":
#             evrythng = 2
#         elif opt == "-f":
#             fforce = True
#         elif opt == "-q":
#             evrythng = 0
#         elif opt == "-v":
#             _module_logger.setLevel(logging.INFO)
#         elif opt == "-V":
#             _module_logger.setLevel(logging.DEBUG)
#         else:
#             _module_logger.error("Invalid option %s", opt)
#
#     tango_host = f"{DATABASEDS_NAME}.{KUBE_NAMESPACE}.svc.{CLUSTER_DOMAIN}:10000"
#     if show_host:
#         print(f"TANGO_HOST={tango_host}")
#         return 0
#
#     os.environ["TANGO_HOST"] = tango_host
#     _module_logger.info("Set TANGO_HOST to %s", tango_host)
#
#     if tgo_attrib is not None:
#         show_attributes(evrythng, fforce, tgo_attrib)
#         return 0
#
#     if tgo_cmd is not None:
#         show_commands(evrythng, fforce, tgo_cmd)
#         return 0
#
#     show_devices(evrythng, fforce, itype)
#
#     return 0
#
#
# if __name__ == "__main__":
#     try:
#         main(sys.argv)
#     except KeyboardInterrupt:
#         pass
