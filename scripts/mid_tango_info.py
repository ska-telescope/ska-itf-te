#!/usr/bin/python
import getopt
import logging
import os
import sys

import tango

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger(__name__)
_module_logger.setLevel(logging.WARNING)


def connect_device(device: str):
    """
    Display Tango device in markdown format

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


def show_device(device: str, fforce: bool) -> int:
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
    # Print commands in italic
    for cmd in cmds:
        print(f"\t\033[3m{cmd}\033[0m")
    # Print attributes in bold
    for attrib in attribs:
        print(f"\t\033[1m{attrib}\033[0m")
    if cmds or attribs:
        return 1
    return 0


def show_device_markdown(device: str) -> int:  # noqa: C901
    """
    Display Tango device in markdown format

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
            print(f"```\n{cmd_cfg}\n```")
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
                print(f"##### Configuration\n\n```\n{attrib_cfg}\n```")
            except Exception:
                print(f"```\n{attrib} configuration could not be read\n```")
    else:
        print("```\nNot reading attributes in offline state\n```")
    print("")
    return rval


def show_devices(evrythng: bool, fforce: bool, itype: str | None) -> None:
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
    except Exception as e:
        _module_logger.error("Could not connect to Tango database %s", tango_host)
        return
    # Read devices
    device_list = database.get_device_exported("*")
    _module_logger.info(f"{len(device_list)} devices available")

    _module_logger.info("Read %d devices" % (len(device_list)))
    if evrythng:
        print("# Tango devices")
        print("## Tango host\n%s```" % tango_host)
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
        if evrythng:
            on_dev_count += show_device_markdown(device)
        else:
            on_dev_count += show_device(device, fforce)

    if evrythng:
        if itype:
            print("## Summary")
            print(f"Found {dev_count} devices matching {itype}")
        else:
            print("## Summary")
            print(f"Found {dev_count} devices")
        print(f"There are {on_dev_count} active devices")
        print("# Kubernetes pod\n>", end="")


def usage(p_name: str) -> None:
    """
    Show how it is done.

    :param p_name: executable name
    """
    print("Display device names only")
    print(f"\t{p_name}")
    print("Display all devices")
    print(f"\t{p_name} -e [-f]")
    print("Filter on device name")
    print(f"\t{p_name} [-f] --device=tmc")
    print(f"\t{p_name} -e [-f] --device=csp")
    print("where:")
    print("\t-e\tread everything and display in markdown format")
    print("\t-f\tget commands and attributes regadrless of state")


def main(y_arg: list) -> int:
    """
    Read and display Tango devices.

    :param y_arg: input arguments
    """
    itype = None
    evrythng = False
    fforce = False
    try:
        opts, _args = getopt.getopt(
            y_arg[1:],
            "efhvVI:",
            ["help", "device="],
        )
    except getopt.GetoptError as opt_err:
        print(f"Could not read command line: {opt_err}")
        return 1

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(os.path.basename(y_arg[0]))
            sys.exit(1)
        elif opt in ("-I", "--device"):
            itype = arg.upper()
        elif opt == "-e":
            evrythng = True
        elif opt == "-f":
            fforce = True
        elif opt == "-v":
            _module_logger.setLevel(logging.INFO)
        elif opt == "-V":
            _module_logger.setLevel(logging.DEBUG)
        else:
            _module_logger.error("Invalid option %s", opt)

    show_devices(evrythng, fforce, itype)
    return 0


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
