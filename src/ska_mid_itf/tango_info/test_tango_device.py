#!/usr/bin/python
"""
Test devices from Tango database.
"""
import getopt
import json
import logging
import os
import sys
import tango
from typing import Any, TextIO, Tuple

from ska_mid_itf.k8s_info.get_k8s_info import KubernetesControl

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger(__name__)
_module_logger.setLevel(logging.WARNING)

KUBE_NAMESPACE = "ci-ska-mid-itf-at-1820-tmc-test-sdp-notebook-v2"
CLUSTER_DOMAIN = "miditf.internal.skao.int"
DATABASEDS_NAME = "tango-databaseds"


class TestTangoDevice:
    """
    Test a Tango device
    """

    def __init__(self, logger: logging.Logger, device_name: str):
        self.logger = logger
        self.adminMode = None
        self.attribs = []
        self.cmds = []
        try:
            self.dev: tango.DeviceProxy = tango.DeviceProxy(device_name)
        except tango.ConnectionFailed:
            print(f"[FAILED] {device_name} connection failed")
            self.dev = None
        except tango.DevFailed:
            print(f"[FAILED] {device_name} device failed")
            self.dev = None
        if self.dev is not None:
            try:
                self.adminMode = self.dev.adminMode
                print(f"[  OK  ] admin mode {self.adminMode}")
            except AttributeError:
                self.adminMode = None
            self.dev_name = self.dev.name()
            self.attribs = self.dev.get_attribute_list()
            self.cmds = self.dev.get_command_list()
        self.dev_status = None
        self.dev_state = None

    def get_admin_mode(self):
        try:
            self.adminMode = self.dev.adminMode
            print(f"[  OK  ] admin mode {self.adminMode}")
        except AttributeError:
            print("[FAILED] could not read admin mode")
            self.adminMode = None
        return self.adminMode

    def check_device(self) -> bool:
        try:
            self.dev.ping()
            print(f"[  OK  ] {self.dev_name} is online")
        except Exception:
            print("[FAILED] {self.dev_name} is not online")
            return False
        return True

    def show_device_attributes(self):
        print(f"[  OK  ] {self.dev_name} has {len(self.attribs)} attributes")
        # print("Attributes")
        # for attrib in self.attribs:
        #     print(f"\t{attrib}")

    def show_device_commands(self):
        print(f"[  OK  ] {self.dev_name} has {len(self.cmds)} commands")
        # print("Commands")
        # for cmd in self.cmds:
        #     print(f"\t{cmd}")

    def admin_mode_off(self):
        if self.adminMode is None:
            return
        if self.adminMode == 1:
            self.logger.info("Turn device admin mode off")
            try:
                self.dev.adminMode = 0
                self.adminMode = self.dev.adminMode
            except tango.DevFailed:
                print(f"[FAILED] {self.dev_name} admin mode could not be turned off")
                return
            self.adminMode = self.dev.adminMode
        print(f"[  OK  ] {self.dev_name} admin mode set to off, now ({self.adminMode})")

    def device_status(self):
        if "Status" not in self.cmds:
            print(f"[FAILED] {self.dev.dev_name} does not have Status command")
        if "State" not in self.cmds:
            print(f"[FAILED] {self.dev.dev_name} does not have State command")
            return None
        self.dev_status = self.dev.Status()
        self.dev_state = self.dev.State()
        print(f"[  OK  ] {self.dev_name} status : {self.dev_status}")
        # print(f"[  OK  ] {self.dev_name} state is {self.dev_state:d}")
        return self.dev_state

    def device_on(self):
        if "On" not in self.cmds:
            print(f"[FAILED] {self.dev.dev_name} does not have On command")
            return
        try:
            dev_on = self.dev.On()
            print(f"[  OK  ] {self.dev_name} turned on, now {dev_on}")
            return
        except tango.DevFailed:
            print(f"[ WARN ] {self.dev_name} retry on command")
        try:
            dev_on = self.dev.On([])
            print(f"[  OK  ] {self.dev_name} turned on, now {dev_on}")
            return
        except tango.DevFailed:
            print(f"[FAILED] {self.dev_name} could not be turned on")

    def device_off(self):
        if "Off" not in self.cmds:
            print(f"[FAILED] {self.dev.dev_name} does not have Off command")
        try:
            dev_off = self.dev.Off()
            print(f"[  OK  ] {self.dev_name} turned off, now {dev_off}")
            return
        except tango.DevFailed:
            print(f"[ WARN ] {self.dev_name} retry off command")
        try:
            dev_off = self.dev.Off([])
            print(f"[  OK  ] {self.dev_name} turned off, now {dev_off}")
            return
        except tango.DevFailed:
            print(f"[FAILED] {self.dev_name} could not be turned off")

    def admin_mode_on(self):
        self.logger.info("Turn device admin mode on")
        try:
            self.dev.adminMode = 1
            self.adminMode = self.dev.adminMode
        except tango.DevFailed:
            print(f"[FAILED] {self.dev_name} admin mode could not be turned on")
            return
        print(f"[  OK  ] {self.dev_name} admin mode turned on, now ({self.adminMode})")


def show_namespaces() -> None:
    """
    Display namespace in Kubernetes cluster.
    """
    k8s = KubernetesControl(_module_logger)
    print("Namespaces:")
    ns_list = k8s.get_namespaces()
    for ns_name in ns_list:
        print(f"{ns_name}")


def get_devices():
    tango_devices = []
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
        tango_devices.append(device)
    return tango_devices


def usage(p_name: str, cfg_data: Any) -> None:
    """
    Show how it is done.

    :param p_name: executable name
    """
    print("Display Kubernetes namespaces")
    print(f"\t{p_name} -n")


def main(y_arg: list) -> int:  # noqa: C901
    """
    Read and display Tango devices.

    :param y_arg: input arguments
    :return: error condition
    """
    global KUBE_NAMESPACE
    dev_name: str | None = None
    disp_action: int = 0
    evrythng: bool = False
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
            "adefghmnqstvVA:C:H:D:N:T:",
            [
                "help",
                "input",
                "host=",
                "device=",
                "attribute=",
                "command=",
                "namespace=",
            ],
        )
    except getopt.GetoptError as opt_err:
        print(f"Could not read command line: {opt_err}")
        return 1

    cfg_name: str | bytes = os.path.basename(y_arg[0]).replace(".py", ".json")
    cfg_file: TextIO = open(f"{os.path.dirname(y_arg[0])}/{cfg_name}")
    cfg_data: Any = json.load(cfg_file)
    cfg_file.close()

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(os.path.basename(y_arg[0]), cfg_data)
            sys.exit(1)
        elif opt in ("-A", "--attribute"):
            tgo_attrib = arg
        elif opt in ("-C", "--command"):
            tgo_cmd = arg
        elif opt in ("-H", "--host"):
            tango_host = arg
        elif opt in ("-D", "--device"):
            dev_name = arg
        elif opt in ("-N", "--namespace"):
            KUBE_NAMESPACE = arg
        elif opt in ("-T", "--input"):
            tgo_in_type = arg.lower()
        elif opt == "-a":
            show_jargon = True
        elif opt == "-t":
            show_tango = True
        elif opt == "-m":
            disp_action = 2
        elif opt == "-f":
            disp_action = 1
        elif opt == "-e":
            evrythng = True
        elif opt == "-n":
            show_ns = True
        elif opt == "-q":
            disp_action = 3
        elif opt == "-d":
            disp_action = 4
        elif opt == "-s":
            disp_action = 5
        elif opt == "-v":
            _module_logger.setLevel(logging.INFO)
        elif opt == "-V":
            _module_logger.setLevel(logging.DEBUG)
        else:
            _module_logger.error("Invalid option %s", opt)

    if show_ns:
        k8s = KubernetesControl(_module_logger)
        print("Namespaces:")
        ns_list = k8s.get_namespaces()
        for ns_name in ns_list:
            print(f"{ns_name}")
        return 0

    if tango_host is None:
        tango_fqdn = f"{DATABASEDS_NAME}.{KUBE_NAMESPACE}.svc.{CLUSTER_DOMAIN}"
        tango_host = f"{tango_fqdn}:10000"
    else:
        tango_fqdn = tango_host.split(":")[0]

    # if show_tango:
    #     check_tango(tango_fqdn)
    #     return 0

    os.environ["TANGO_HOST"] = tango_host
    _module_logger.info("Set TANGO_HOST to %s", tango_host)

    print(f"[  OK  ] Namespace {KUBE_NAMESPACE}")

    if dev_name is not None:
        dev_test = TestTangoDevice(_module_logger, dev_name)
        if dev_test.dev is None:
            print(f"[FAILED] could not open device {dev_name}")
            return 1
        dev_test.check_device()
        dev_test.show_device_attributes()
        dev_test.show_device_commands()
        # Read admin mode, turn on ond off
        init_admin_mode = dev_test.get_admin_mode()
        dev_test.admin_mode_on()
        dev_test.admin_mode_off()
        # Read state
        init_state = dev_test.device_status()
        # Turn device on
        if init_state == tango._tango.DevState.ON:
            print(f"[ WARN ] device is already on")
        else:
            dev_test.device_on()
        dev_test.device_status()
        # Turn device off
        dev_test.device_off()
        dev_test.device_status()
        if dev_test.dev_state == tango._tango.DevState.ON:
            print(f"[FAILED] device is still on")
        # Turn device back on, if neccesary
        if init_state == tango._tango.DevState.ON:
            print(f"[ WARN ] turn device back on")
            dev_test.device_on()
            dev_test.device_status()
        # Turn device admin mode back on, if neccesary
        if init_admin_mode == 1:
            print("[ WARN ] turn admin mode back to on")
            dev_test.admin_mode_on()
        return 0

    devices = get_devices()
    for device in devices:
        print(f"\t{device}")

    return 0


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
