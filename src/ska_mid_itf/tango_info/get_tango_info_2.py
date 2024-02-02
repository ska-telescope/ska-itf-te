#!/usr/bin/python
"""
Read information from Tango database.
"""
import getopt
import json
import logging
import os
import socket
import sys
import time
from typing import Any, Tuple

import tango
from ska_control_model import AdminMode
from ska_mid_itf.k8s_info.get_k8s_info import KubernetesControl
from ska_mid_itf.ska_jargon.ska_jargon import find_jargon, print_jargon

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger(__name__)
_module_logger.setLevel(logging.WARNING)

KUBE_NAMESPACE = "ci-ska-mid-itf-at-1820-tmc-test-sdp-notebook-v2"
CLUSTER_DOMAIN = "miditf.internal.skao.int"
DATABASEDS_NAME = "tango-databaseds"


def check_tango(tango_fqdn: str, tango_port: int = 10000) -> int:
    """
    Check Tango host address.

    :param tango_fqdn: fully qualified domain name
    :param tango_port: port number
    :return: error condition
    """
    try:
        tango_addr = socket.gethostbyname_ex(tango_fqdn)
        tango_ip = tango_addr[2][0]
    except socket.gaierror as e:
        print("Could not read address %s : %s" % (tango_fqdn, e))
        return 1
    print(f"TANGO_HOST={tango_fqdn}:{tango_port}")
    print(f"TANGO_HOST={tango_ip}:{tango_port}")
    return 0


def show_namespaces():
    k8s = KubernetesControl(_module_logger)
    print("Namespaces:")
    ns_list = k8s.get_namespaces()
    for ns_name in ns_list:
        print(f"{ns_name}")


class TangoDeviceInfo():

    def __init__(self, device_name: str, evrythng: int, fforce: bool):
        """
        Display Tango device in mark-down format

        :param device_name: device name
        :param evrythng: flag for output format
        :param fforce: get commands and attributes regadrless of state
        """
        # Connect to device proxy
        self.dev: tango.DeviceProxy = tango.DeviceProxy(device_name)
        # Read state
        try:
            self.dev_state = self.dev.State()
        except Exception:
            self.dev_state = None
        try:
            self.dev_name = self.dev.name()
            self.online = True
        except Exception:
            self.dev_name = device_name
            self.online = False
        self.evrythng = evrythng
        self.fforce = fforce
        self.on_dev_count = 0

    def check_device(self) -> bool:
        try:
            self.dev.ping()
            return True
        except Exception:
            return False

    def device_state(self) -> None:
        """
        Display status information for Tango device.

        :param dev: Tango device handle
        :return: None
        """
        print(f"Device {self.dev_name}")
        if not self.online:
            return
        print(f"\tAdmin mode                     : {self.dev.adminMode}")
        print(f"\tDevice status                  : {self.dev.Status()}")
        print(f"\tDevice state                   : {self.dev.State()}")
        try:
            print(f"\tObservation state              : {repr(self.dev.obsState)}")
            show_obs_state(self.dev.obsState)
        except AttributeError:
            _module_logger.info(
                "Device %s does not have an observation state", self.dev_name
            )
        print(f"versionId                        : {self.dev.versionId}")
        print(f"build State                      : {self.dev.buildState}")
        print(f"logging level                    : {self.dev.loggingLevel}")
        print(f"logging Targets                  : {self.dev.loggingTargets}")
        print(f"health State                     : {self.dev.healthState}")
        print(f"control Mode                     : {self.dev.controlMode}")
        print(f"simulation Mode                  : {self.dev.simulationMode}")
        print(f"test Mode                        : {self.dev.testMode}")
        print(
            f"long Running Commands In Queue   : {self.dev.longRunningCommandsInQueue}"
        )
        print(
            f"long Running Command IDs InQueue : {self.dev.longRunningCommandIDsInQueue}"
        )
        print(f"long Running Command Status      : {self.dev.longRunningCommandStatus}")
        print(
            f"long Running Command Progress    : {self.dev.longRunningCommandProgress}"
        )
        print(
            f"long Running Command Result      : {self.dev.longRunningCommandResult}"
        )

    def get_tango_admin(self) -> bool:
        """
        Read admin mode for Tango device.

        :return: True when device is in admin mode
        """
        csp_admin = self.dev.adminMode
        if csp_admin == AdminMode.ONLINE:
            print("Device admin mode online")
            return False
        if csp_admin == AdminMode.OFFLINE:
            print("Device admin mode offline")
        else:
            print(f"Device admin mode {csp_admin}")
        return True

    def set_tango_admin(self, dev_adm: bool, sleeptime: int = 2) -> bool:
        """
        Write admin mode for a Tango device.

        :param dev_adm: admin mode flag
        :param sleeptime: seconds to sleep
        :return: True when device is in admin mode
        """
        print(f"*** Set Adminmode to {dev_adm} and check state ***")
        if dev_adm:
            self.dev.adminMode = 1
        else:
            self.dev.adminMode = 0
        time.sleep(sleeptime)
        return self.get_tango_admin()

    def run_command(self, cmd: str) -> None:
        """
        Run command and get output.
        :param cmd: command name
        :return: None
        """
        if cmd in SAFE_COMMANDS:
            try:
                inout = self.dev.command_inout(cmd)
            except tango.DevFailed:
                print(f"{cmd:17} : error")
                return
            print(f"{cmd:17} : {inout}")
        else:
            print(f"{'Query sub-devices':17} : N/A")

    def show_device_command(self, prefix, cmd) -> None:
        lpre = "\n" + f"{' ':67}"
        print(f"{prefix:17}   \033[3m{cmd.cmd_name:30}\033[0m", end="")
        if self.dev.is_command_polled(cmd.cmd_name):
            print(" Polled     ", end="")
        else:
            print(" Not polled ", end="")
        in_type_desc = cmd.in_type_desc
        if in_type_desc != "Uninitialised":
            if "\n" in in_type_desc:
                in_type_desc = in_type_desc[:-1].replace('\n', lpre)
            print(f" IN  {in_type_desc}")
        else:
            in_type_desc = ""
        out_type_desc = cmd.out_type_desc
        if out_type_desc != "Uninitialised":
            if in_type_desc:
                print(f"{' ':63}", end="")
            else:
                print(" ", end="")
            if "\n" in out_type_desc:
                out_type_desc = out_type_desc[:-1].replace('\n', lpre)
            print(f"OUT {out_type_desc}")
        else:
            out_type_desc = ""
        if in_type_desc == "" and out_type_desc == "":
            print()
        if self.fforce and in_type_desc == "Uninitialised":
            run_cmd = self.dev.command_inout(cmd)

    def show_device_commands(self) -> None:
        """
        Print commands.
        :return: None
        """
        try:
            cmds = self.dev.get_command_config()
        except Exception:
            cmds = []
        if cmds:
            cmd = cmds[0]
            self.show_device_command("Commands", cmd)
            for cmd in cmds[1:]:
                self.show_device_command(" ", cmd)

    def show_attribute_value_scalar(self, prefix: str, attrib_value: str):
        """
        Print attribute value.
        :param prefix: data prefix string
        :param attrib_value: attribute value
        """
        try:
            attrib_json = json.loads(attrib_value)
        except Exception:
            print(f" {attrib_value}")
            return
        print()
        if type(attrib_json) is dict:
            for value in attrib_json:
                attr_value = attrib_json[value]
                if type(attr_value) is list:
                    for item in attr_value:
                        if type(item) is dict:
                            print(f"{prefix} {value} :")
                            for key in item:
                                print(f"{prefix+'    '} {key} : {item[key]}")
                        else:
                            print(f"{prefix+'    '} {item}")
                elif type(attr_value) is dict:
                    print(f"{prefix} {value}")
                    for key in attr_value:
                        key_value = attr_value[key]
                        if not key_value:
                            print(f"{prefix+'    '} {key} ?")
                        elif type(key_value) is str:
                            if key_value[0] == "{":
                                print(f"{prefix+'    '} {key} : DICT{key_value}")
                            else:
                                print(f"{prefix+'    '} {key} : STR{key_value}")
                        else:
                            print(f"{prefix+'    '} {key} : {key_value}")
                else:
                    print(f"{prefix} {value} : {attr_value}")
        elif type(attrib_json) is list:
            for value in attrib_json:
                print(f"{prefix} {value}")
        else:
            print(f" {attrib_value} {type(attrib_value)}")

    def show_attribute_value_spectrum(self, prefix: str, attrib_value: str):
        """
        Print attribute value
        :param prefix: data prefix string
        :param attrib_value: attribute value
        """
        if not attrib_value:
            print(" <EMPTY>")
        elif type(attrib_value) is tuple:
            print()
            for attr in attrib_value:
                print(f"{prefix}   {attr}")
        elif type(attrib_value) is dict:
            int_models = json.loads(attrib_value)
            for key in int_models:
                print(f"{prefix}   {key}")
                int_model_values = int_models[key]
                if type(int_model_values) is dict:
                    for value in int_model_values:
                        print(f"{prefix+'     '} {value} : {int_model_values[value]}")
                else:
                    print(f"{prefix+'     '} {value} : {int_model_values}")
        else:
            print(f" {type(attrib_value)}:{attrib_value}")

    def show_attribute_value(self, attrib: str, prefix: str):
        """
        Print attribute value
        :param attrib: attribute name
        :param prefix: data prefix string
        """
        try:
            attrib_value = self.dev.read_attribute(attrib).value
        except Exception:
            print(" <could not be read>")
            return
        _module_logger.debug("Attribute %s value %s", attrib, attrib_value)
        attrib_cfg = self.dev.get_attribute_config(attrib)
        data_format = attrib_cfg.data_format
        print(f" ({data_format})", end="")
        if data_format == tango._tango.AttrDataFormat.SCALAR:
            self.show_attribute_value_scalar(prefix, attrib_value)
        elif data_format == tango._tango.AttrDataFormat.SPECTRUM:
            self.show_attribute_value_spectrum(prefix, attrib_value)
        else:
            print(f" {attrib_value}")
        events = attrib_cfg.events.arch_event.archive_abs_change
        print(f"{prefix} Event change : {events}")
        print(f"{prefix} Quality : {self.dev.read_attribute(attrib).quality}")
        print(f"{prefix} Polled: {self.dev.is_attribute_polled(attrib)}")

    def show_device_attributes(self) -> None:
        """
        Print attributes
        :return: None
        """
        try:
            attribs = sorted(self.dev.get_attribute_list())
        except Exception:
            attribs = []
        if attribs:
            attrib = attribs[0]
            print(f"{'Attributes':17} : \033[1m{attrib}\033[0m", end="")
            self.show_attribute_value(attrib, ' ' * 25)
            for attrib in attribs[1:]:
                print(
                    f"{' ':17}   \033[1m{attrib}\033[0m ", end=""
                )
                self.show_attribute_value(attrib, ' ' * 25)

    def show_device_query(self) -> int:  # noqa: C901
        """
        Display Tango device in text format

        :return: one if device is on, otherwise zero
        """
        rv = 1
        # pylint: disable-next=c-extension-no-member
        print(f"{'Device':17} : {self.dev_name}", end="")
        if not self.online:
            print(" error")
            return 0
        if self.dev_state != tango._tango.DevState.ON:
            if not self.fforce:
                print(f"\n{'State':17} : OFF\n")
                return 0
            rv = 0
        try:
            cmds = self.dev.get_command_list()
        except Exception:
            cmds = []
        print(f" {len(cmds)} \033[3mcommands\033[0m,", end="")
        try:
            attribs = sorted(self.dev.get_attribute_list())
        except Exception:
            attribs = []
        print(f" {len(attribs)} \033[1mattributes\033[0m")
        dev_info = self.dev.info()
        if "State" in cmds:
            print(f"{'State':17} : {self.dev.State()}")
        if "Status" in cmds:
            dev_status = self.dev.Status().replace("\n", f"\n{' ':20}")
            print(f"{'Status':17} : {dev_status}")
        print(f"{'Description':17} : {self.dev.description()}")
        jargon = find_jargon(self.dev_name)
        if jargon:
            print(f"{'Acronyms':17} : {jargon}")
        print(f"{'Device class':17} : {dev_info.dev_class}")
        print(f"{'Server host':17} : {dev_info.server_host}")
        print(f"{'Server ID':17} : {dev_info.server_id}")
        if "DevLockStatus" in cmds:
            print(f"{'Lock status':17} : {self.dev.DevLockStatus(self.dev_name)}")
        if "DevPollStatus" in cmds:
            print(f"{'Poll status':17} : {self.dev.DevPollStatus(self.dev_name)}")
        # Get Logging Target
        if "GetLoggingTarget" in cmds:
            qdevs = self.dev.GetLoggingTarget(self.dev_name)
            if qdevs:
                qdev = qdevs[0]
                print(f"{'Logging target':17} : {qdev}")
                for qdev in qdevs[1:]:
                    print(f"{' ':17} : {qdev}")
            else:
                print(f"{'Logging target':17} : none specified")
        # else:
        #     print(f"{'Logging target':17} : N/A")
        # Print query classes
        if "QueryClass" in cmds:
            qdevs = self.dev.QueryClass()
            if qdevs:
                qdev = qdevs[0]
                print(f"{'Query class':17} : {qdev}")
                for qdev in qdevs[1:]:
                    print(f"{' ':17} : {qdev}")
            else:
                print(f"{'Query class':17} : none specified")
        # else:
        #     print(f"{'Query class':17} : N/A")
        # Print query devices
        if "QueryDevice" in cmds:
            qdevs = self.dev.QueryDevice()
            if qdevs:
                qdev = qdevs[0]
                print(f"{'Query devices':17} : {qdev}")
                for qdev in qdevs[1:]:
                    print(f"{' ':17} : {qdev}")
            else:
                print(f"{'Query devices':17} : none specified")
        # else:
        #     print(f"{'Query devices':17} : N/A")
        # Print query sub-devices
        if "QuerySubDevice" in cmds:
            qdevs = self.dev.QuerySubDevice()
            if qdevs:
                qdev = qdevs[0]
                print(f"{'Query sub-devices':17} : {qdev}")
                for qdev in qdevs[1:]:
                    print(f"{' ':17} : {qdev}")
            else:
                print(f"{'Query sub-devices':17} : none specified")
        # else:
        #     print(f"{'Query sub-devices':17} : N/A")
        print("")
        return rv

    def show_device_all(self) -> int:  # noqa: C901
        """
        Display Tango device in text format
        :return: one if device is on, otherwise zero
        """
        # pylint: disable-next=c-extension-no-member
        print(f"{'Device':17} : {self.dev_name}", end="")
        if not self.online:
            print(" error")
            return 0
        rv = 1
        if self.dev_state != tango._tango.DevState.ON:
            if not self.fforce:
                print(f"\n{'State':17} : OFF\n")
                return 0
            rv = 0
        # else:
        #     print(f" <ON>", end="")
        try:
            cmds = self.dev.get_command_list()
        except Exception:
            cmds = []
        print(f" {len(cmds)} \033[3mcommands\033[0m,", end="")
        try:
            attribs = sorted(self.dev.get_attribute_list())
        except Exception:
            attribs = []
        print(f" {len(attribs)} \033[1mattributes\033[0m")
        dev_info = self.dev.info()
        if "State" in cmds:
            print(f"{'State':17} : {self.dev.State()}")
        if "Status" in cmds:
            dev_status = self.dev.Status().replace("\n", f"\n{' ':20}")
            print(f"{'Status':17} : {dev_status}")
        print(f"{'Description':17} : {self.dev.description()}")
        jargon = find_jargon(self.dev_name)
        if jargon:
            print(f"{'Acronyms':17} : {jargon}")
        print(f"{'Database used':17} : {self.dev.is_dbase_used()}")
        print(f"{'Device class':17} : {dev_info.dev_class}")
        print(f"{'Server host':17} : {dev_info.server_host}")
        print(f"{'Server ID':17} : {dev_info.server_id}")
        try:
            print(f"{'Resources'} : {self.dev.assignedresources}")
        except tango.DevFailed:
            print("{'Resources':17} : could not be read")
        except AttributeError:
            pass
        try:
            print(f"{'VCC state':17} : {self.dev.assignedVccState}")
        except AttributeError:
            pass
        try:
            dev_obs = self.dev.obsState
            print(f"{'Observation':17} : {get_obs_state(dev_obs)}")
        except Exception:
            pass
        # Print commands in italic
        self.show_device_commands()
        if "DevLockStatus" in cmds:
            # run_command(dev, "DevLockStatus")
            print(f"{'Lock status':17} : {self.dev.DevLockStatus(self.dev_name)}")
        if "DevPollStatus" in cmds:
            print(f"{'Poll status':17} : {self.dev.DevPollStatus(self.dev_name)}")
        # Get Logging Target
        if "GetLoggingTarget" in cmds:
            qdevs = self.dev.GetLoggingTarget(self.dev_name)
            if qdevs:
                qdev = qdevs[0]
                print(f"{'Logging target':17} : {qdev}")
                for qdev in qdevs[1:]:
                    print(f"{' ':17} : {qdev}")
            else:
                print(f"{'Logging target':17} : none specified")
        else:
            print(f"{'Logging target':17} : N/A")
        # Print query classes
        if "QueryClass" in cmds:
            qdevs = self.dev.QueryClass()
            if qdevs:
                qdev = qdevs[0]
                print(f"{'Query class':17} : {qdev}")
                for qdev in qdevs[1:]:
                    print(f"{' ':17} : {qdev}")
            else:
                print(f"{'Query class':17} : none specified")
        else:
            print(f"{'Query class':17} : N/A")
        # Print query devices
        if "QueryDevice" in cmds:
            qdevs = self.dev.QueryDevice()
            if qdevs:
                qdev = qdevs[0]
                print(f"{'Query devices':17} : {qdev}")
                for qdev in qdevs[1:]:
                    print(f"{' ':17} : {qdev}")
            else:
                print(f"{'Query devices':17} : none specified")
        else:
            print(f"{'Query devices':17} : N/A")
        # Print query sub-devices
        if "QuerySubDevice" in cmds:
            qdevs = self.dev.QuerySubDevice()
            if qdevs:
                qdev = qdevs[0]
                print(f"{'Query sub-devices':17} : {qdev}")
                for qdev in qdevs[1:]:
                    print(f"{' ':17} : {qdev}")
            else:
                print(f"{'Query sub-devices':17} : none specified")
        else:
            print(f"{'Query sub-devices':17} : N/A")
        # Print attributes in bold
        self.show_device_attributes()
        return rv

    def show_device_markdown(self) -> int:  # noqa: C901
        """
        Display Tango device in mark-down format.
        """
        rval = 0
        print(f"## Device *{self.dev_name}*")
        if not self.online:
            print("Error")
            return rval
        # Read database host
        print(f"### Database host\n{self.dev.get_db_host()}")
        if self.dev_state is not None:
            print(f"### State\n{self.dev_state}")
        else:
            print("### State\nNONE")
        # Read information
        try:
            print(f"### Information\n```\n{self.dev.info()}\n```")
        except Exception:
            print("### Information\n```\nNONE\n```")
        # Read commands
        try:
            cmds = sorted(self.dev.get_command_list())
            # Display version information
            if "GetVersionInfo" in cmds:
                verinfo = self.dev.GetVersionInfo()
                print(f"### Version\n```\n{verinfo[0]}\n```")
            # Display commands
            print("### Commands")
            print("```\n%s\n```" % "\n".join(cmds))
            # Read command configuration
            cmd_cfgs = self.dev.get_command_config()
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
            print(f"#### Status\n{self.dev.Status()}")
        else:
            print("#### Status\nNo Status command")
        # Read attributes
        print("### Attributes")
        # pylint: disable-next=c-extension-no-member
        if self.dev_state == tango._tango.DevState.ON:
            rval = 1
            attribs = sorted(self.dev.get_attribute_list())
            print("```\n%s\n```" % "\n".join(attribs))
            for attrib in attribs:
                print(f"#### Attribute *{attrib}*")
                try:
                    print(
                        f"##### Value\n```\n{self.dev.read_attribute(attrib).value}\n```"
                    )
                except Exception:
                    print(f"```\n{attrib} could not be read\n```")
                try:
                    attrib_cfg = self.dev.get_attribute_config(attrib)
                    print(f"##### Description\n```\n{attrib_cfg.description}\n```")
                    # print(f"##### Configuration\n```\n{attrib_cfg}\n```")
                except Exception:
                    print(f"```\n{attrib} configuration could not be read\n```")
        else:
            print("```\nNot reading attributes in offline state\n```")
        print("")
        return rval

    def show_device_state(self) -> int:
        """
        Display Tango device name only.
        """
        # pylint: disable-next=c-extension-no-member
        if self.dev_state != tango._tango.DevState.ON:
            print(f"     {self.dev_name}")
            return 0
        print(f"[ON] {self.dev_name}")
        return 1

    def show_device(self):
        """Print device information."""
        if self.evrythng == 4:
            self.on_dev_count += self.show_device_state()
        elif self.evrythng == 3:
            self.on_dev_count += self.show_device_query()
        elif self.evrythng == 2:
            self. on_dev_count += self.show_device_markdown()
        elif self.evrythng == 1:
            self.on_dev_count += self.show_device_all()
        else:
            print("Nothing to do!")

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


SAFE_COMMANDS = ["DevLockStatus"]


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
        # if device[0:4] == "sys/":
        #     _module_logger.info(f"Skip {device}")
        #     continue
        # Check device name against mask
        if itype:
            iupp = device.upper()
            if itype not in iupp:
                _module_logger.info(f"Ignore {device}")
                continue
        dev_count += 1
        try:
            tgo_info = TangoDeviceInfo(device, evrythng, fforce)
        except tango.DevFailed as terr:
            print(f"{device} : {terr}")
        tgo_info.show_device()

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
        # dev, _dev_state = connect_device(device)
        dev: tango.DeviceProxy = tango.DeviceProxy(device)
        try:
            attribs = sorted(dev.get_attribute_list())
        except Exception:
            attribs = []
        if a_name in attribs:
            print(f"* {device:48}", end="")
            print(f" \033[1m{a_name}\033[0m")


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
        # dev, _dev_state = connect_device(device)
        dev: tango.DeviceProxy = tango.DeviceProxy(device)
        chk_cmd = check_command(dev, c_name)
        if chk_cmd:
            print(f"* {dev.name():44}", end="")
            print(f" \033[1m{c_name}\033[0m")


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


def usage(p_name: str) -> None:
    """
    Show how it is done.

    :param p_name: executable name
    """
    print("Display Kubernetes namespaces")
    print(f"\t{p_name} -n")
    print("Display Tango database address")
    print(f"\t{p_name} -t [--namespace=<NAMESPACE>|--host=<HOST>]")
    print(f"\t{p_name} -t [-N <NAMESPACE>|-H <HOST>]")
    print("Display all devices")
    print(f"\t{p_name} -e|-m|-q|-s [-g] [--namespace=<NAMESPACE>|--host=<HOST>]")
    print(f"\t{p_name} -e|-m|-q|-s [-g] [-N <NAMESPACE>|-H <HOST>]")
    print("Filter on device name")
    print(f"\t{p_name} -e|-m|-q|-s [-g] -D <DEVICE> [-N <NAMESPACE>|-H <HOST>]")
    print(
        f"\t{p_name} -e|-m|-q|-s [-g] --device=<DEVICE>"
        " [--namespace=<NAMESPACE>|--host=<HOST>]"
    )
    print("Filter on attribute name")
    print(
        f"\t{p_name} -e|-m|-q|-s [-g] --attribute=<ATTRIBUTE>"
        " [--namespace=<NAMESPACE>|--host=<HOST>]"
    )
    print(
        f"\t{p_name} -e|-m|-q|-s [-g] -A <ATTRIBUTE>"
        " [-N <NAMESPACE>|-H <HOST>]"
    )
    print("Filter on command name")
    print(
        f"\t{p_name} -e|-m|-q|-s [-g] --command=<COMMAND>"
        " [--namespace=<NAMESPACE>|--host=<HOST>]"
    )
    print(
        f"\t{p_name} -e|-m|-q|-s [-g] -C <COMMAND>"
        " [-N <NAMESPACE>|-H <HOST>]"
    )
    print("Display known acronyms")
    print(f"\t{p_name} -a")
    print("where:")
    print("\t-e\t\t\t\tdisplay in text format")
    print("\t-q\t\t\t\tdisplay device name, status and query devices")
    print("\t-d\t\t\t\tdisplay device name and status only")
    # print("\t-m\t\t\t\tdisplay in markdown format")
    print("\t-f\t\t\t\tget commands and attributes regadrless of state")
    print(
        "\t--device=<DEVICE>\t\tdevice name, e.g. 'csp'"
        " (not case sensitive, only a part is needed)"
    )
    print(
        "\t--namespace=<NAMESPACE>\t\tKubernetes namespace for Tango database,"
        " e.g. 'integration'"
    )
    print("\t--host=<HOST>\t\t\tTango database host and port, e.g. 10.8.13.15:10000")
    print(
        "\t--attribute=<ATTRIBUTE>\t\tattribute name, e.g. 'obsState' (case sensitive)"
    )
    print("\t--command=<COMMAND>\t\tcommand name, e.g. 'Status' (case sensitive)")

    print(
        "\t-D <DEVICE>\t\t\tdevice name, e.g. 'csp'"
        " (not case sensitive, only a part is needed)"
    )
    print(
        "\t-N <NAMESPACE>\t\t\tKubernetes namespace for Tango database,"
        " e.g. 'integration'"
    )
    print("\t-H <HOST>\t\t\tTango database host and port, e.g. 10.8.13.15:10000")
    print("\t-A <ATTRIBUTE>\t\t\tattribute name, e.g. 'obsState' (case sensitive)")
    print("\t-C <COMMAND>\t\t\tcommand name, e.g. 'Status' (case sensitive)")


def show_command_inputs(tango_host: str, tgo_in_type: str) -> None:
    """
    Display commands with given input type.
    :param tango_host: Tango database host address and port
    :param tgo_in_type: input type, e.g. Uninitialised
    :return:
    """

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
        try:
            cmds = dev.get_command_config()
        except Exception:
            cmds = []
        if cmds:
            for cmd in cmds:
                in_type_desc = cmd.in_type_desc.lower()
                _module_logger.info("Command %s type %s", cmd, in_type_desc)
                if in_type_desc == tgo_in_type:
                    print(
                        f"{'Commands':17} : \033[3m{cmd.cmd_name}\033[0m ({in_type_desc})")
                else:
                    print(f"{'Commands':17} : {cmd.cmd_name} ({in_type_desc})")
    return

def main(y_arg: list) -> int:  # noqa: C901
    """
    Read and display Tango devices.

    :param y_arg: input arguments
    :return: error condition
    """
    global KUBE_NAMESPACE

    itype: str | None = None
    evrythng: int = 0
    fforce: bool = False
    show_jargon: bool = False
    show_ns: bool = False
    show_tango: bool = False
    tgo_attrib: str | None = None
    tgo_cmd: str | None = None
    tgo_in_type: str | None = None
    tango_host: str | None = None
    try:
        opts, _args = getopt.getopt(
            y_arg[1:],
            "adefghmnqtvVA:C:H:D:N:T:",
            ["help", "input", "host=", "device=", "attribute=", "command=", "namespace="],
        )
    except getopt.GetoptError as opt_err:
        print(f"Could not read command line: {opt_err}")
        return 1

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(os.path.basename(y_arg[0]))
            sys.exit(1)
        elif opt in ("-A", "--attribute"):
            tgo_attrib = arg
        elif opt in ("-C", "--command"):
            tgo_cmd = arg
        elif opt in ("-H", "--host"):
            tango_host = arg
        elif opt in ("-D", "--device"):
            itype = arg.upper()
        elif opt in ("-N", "--namespace"):
            KUBE_NAMESPACE = arg
        elif opt in ("-T", "--input"):
            tgo_in_type = arg.lower()
        elif opt == "-a":
            show_jargon = True
        elif opt == "-t":
            show_tango = True
        elif opt == "-m":
            evrythng = 2
        elif opt == "-e":
            evrythng = 1
        elif opt == "-f":
            fforce = True
        elif opt == "-n":
            show_ns = True
        elif opt == "-q":
            evrythng = 3
        elif opt == "-d":
            evrythng = 4
        elif opt == "-v":
            _module_logger.setLevel(logging.INFO)
        elif opt == "-V":
            _module_logger.setLevel(logging.DEBUG)
        else:
            _module_logger.error("Invalid option %s", opt)

    if show_jargon:
        print_jargon()
        return 0

    if show_ns:
        show_namespaces()
        return 0

    if tango_host is None:
        tango_fqdn = f"{DATABASEDS_NAME}.{KUBE_NAMESPACE}.svc.{CLUSTER_DOMAIN}"
        tango_host = f"{tango_fqdn}:10000"
    else:
        tango_fqdn = tango_host.split(":")[0]

    if show_tango:
        check_tango(tango_fqdn)
        return 0

    os.environ["TANGO_HOST"] = tango_host
    _module_logger.info("Set TANGO_HOST to %s", tango_host)

    if tgo_attrib is not None:
        show_attributes(evrythng, fforce, tgo_attrib)
        return 0

    if tgo_cmd is not None:
        show_commands(evrythng, fforce, tgo_cmd)
        return 0

    if tgo_in_type is not None:
        show_command_inputs(tango_host, tgo_in_type)
        return 0

    if not evrythng:
        print("Nothing to do!")
        return 1

    show_devices(evrythng, fforce, itype)

    return 0


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
