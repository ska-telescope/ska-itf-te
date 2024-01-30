#!/usr/bin/python
"""
Start and stop Central Signal Processor (CSP) or Telescope Monitor and Control (TMC).

Use to test functionality used in notebooks.

CSP assign resources:
https://developer.skao.int/projects/ska-telmodel/en/latest/schemas/ska-csp-assignresources.html
CSP configure:
https://developer.skao.int/projects/ska-telmodel/en/latest/schemas/ska-csp-configure.html
CSP scan:
https://developer.skao.int/projects/ska-telmodel/en/latest/schemas/ska-csp-scan.html
CSP end scan:
https://developer.skao.int/projects/ska-telmodel/en/latest/schemas/ska-csp-endscan.html
CSP release resources:
https://developer.skao.int/projects/ska-telmodel/en/latest/schemas/ska-csp-releaseresources.html
CSP delay model:
https://developer.skao.int/projects/ska-telmodel/en/latest/schemas/ska-csp-delaymodel.html
"""
import datetime
import getopt
import json
import logging
import os
import pprint
import socket
import sys
import time
from typing import Any, List, Tuple

import ska_ser_logging  # type: ignore[import]
import tango
from k8s_info.get_k8s_info import KubernetesControl
from tango_info.get_tango_info import (
    check_device,
    check_tango,
    device_state,
    set_tango_admin,
    setup_device,
    show_long_running_command,
    show_long_running_commands,
    show_obs_state,
)

from ska_mid_itf.ska_jargon.ska_jargon import get_ska_jargon

ska_ser_logging.configure_logging(logging.DEBUG)
_module_logger: logging.Logger = logging.getLogger(__name__)

# LONG_RUN_CMDS: int = 4
#
# LEAFNODE_DEVICE = "ska_mid/tm_leaf_node/csp_subarray_01"
# BITE_POD = "ec-bite"
# BITE_CMD = ["python3", "midcbf_bite.py", "--talon-bite-lstv-replay", "--boards=1"]
# TIMEOUT = 60



CONFIGUREDATA: Any = {
    "interface": "https://schema.skao.int/ska-csp-configure/2.3",
    "subarray": {"subarray_name": "Single receptor"},
    "common": {
        "config_id": "1 receptor, band 1, 1 FSP, no options",
        "frequency_band": "1",
        "subarray_id": 0,
    },
    "cbf": {
        "delay_model_subscription_point": (
            "ska_mid/tm_leaf_node/csp_subarray_01/delayModel",
        ),
        "rfi_flagging_mask": {},
        "fsp": [
            {
                "fsp_id": 1,
                "function_mode": "CORR",
                "receptors": ["SKA001"],
                "frequency_slice_id": 1,
                "zoom_factor": 1,
                "zoom_window_tuning": 450000,
                "integration_factor": 10,
                "channel_offset": 14880,
                "output_link_map": [
                    [0, 4],
                    [744, 8],
                    [1488, 12],
                    [2232, 16],
                    [2976, 20],
                    [3720, 24],
                    [4464, 28],
                    [5206, 32],
                    [5952, 36],
                    [6696, 40],
                    [7440, 44],
                    [8184, 48],
                    [8928, 52],
                    [9672, 56],
                    [10416, 60],
                    [11160, 64],
                    [11904, 68],
                    [12648, 72],
                    [13392, 76],
                    [14136, 80],
                ],
                "output_host": [[0, "10.165.20.31"]],
                "output_port": [[0, 14000, 1]],
            }
        ],
    },
}


def log_prog(log_str: str) -> None:
    """
    Display progess heading.
    :param log_str: message to display
    :return: None
    """
    print("_" * len(log_str))
    print(log_str)


def read_config_json(json_name: str) -> Any:
    """
    Read configuration from JSON file.

    :param json_name: configuration file name
    :return: configuration data
    """
    # print(f"Read configuration file {json_name}")
    cfg_file = open(json_name)
    cfg_data = json.load(cfg_file)
    return cfg_data


def show_config_json(sub_sys: str, json_cfg: Any) -> None:
    """
    Display configuration from JSON file.

    :param mid_sys: subsystem name,e.g. CSP
    :param json_cfg: configuration data
    :return: None
    """
    log_prog("Configuration")
    print(f"\tkube namespace  : {json_cfg['kube_namespace']}")
    print(f"\tcluster domain  : {json_cfg['cluster_domain']}")
    print(f"\tdatabaseds name : {json_cfg['databaseds_name']}")
    print(f"\tsubsystem       : {sub_sys.upper()}")
    log_prog(f"Subsystem configuration: {sub_sys.upper()}")
    try:
        print(f"\tcontrol device  : {json_cfg[sub_sys]['control_device']}")
        print(f"\tsubarray device : {json_cfg[sub_sys]['subarray_device']}")
        print(f"\tleafnode device : {json_cfg[sub_sys]['leafnode_device']}")
        print(f"\tbite pod        : {json_cfg[sub_sys]['bite_pod']}")
        print(f"\tbite command    : {' '.join(json_cfg[sub_sys]['bite_cmd'])}")
    except TypeError:
        pass
    # print(f"{json_cfg[mid_sys]['']}")


def show_observation_status(sub_dev_name: str) -> int:
    """

    :param sub_dev_name: Tango device name
    :return: error condtion
    """
    _rc, dev = setup_device(sub_dev_name)
    if dev is None:
        return 1
    dev_obs = dev.obsState
    show_obs_state(dev_obs)
    return 0


def init_device(dev: tango.DeviceProxy, timeout: int, dev_sim: bool) -> int:
    """
    Set up device connection and timeouts.

    :param dev: Tango device handle
    :param timeout: in seconds
    :param dev_sim: simulate Correlator Beam Former (CBF)
    :return: error condition
    """
    dev_name = dev.name()
    log_prog(f"Initialize device {dev_name}")
    print(f"Status : {dev.Status()}")
    csp_state = dev.State()
    print(f"Device state : {csp_state}")
    # pylint: disable-next=c-extension-no-member
    if csp_state == tango._tango.DevState.OFF:
        print("Device %s is off" % dev_name)
        _csp_admin = set_tango_admin(dev, False)  # noqa: F841
        csp_state = dev.State()
        # pylint: disable-next=c-extension-no-member
        if csp_state != tango._tango.DevState.ON:
            print("Device %s is off" % dev_name)
            return 1
    # pylint: disable-next=c-extension-no-member
    elif csp_state == tango._tango.DevState.ON:
        print("Device %s is on" % dev_name)
    else:
        print("Device %s state is %s" % (dev_name, str(csp_state)))
    # Set Timeout to 60 seconds as the ON command is a long-running command
    dev.commandTimeout = timeout
    # check value
    print(f"Command timeout is {dev.commandTimeout}")
    # Check CBF SimulationMode (this should be FALSE for real hardware control)
    print(f"Set device simulation mode to {dev_sim}")
    dev.cbfSimulationMode = dev_sim
    if dev.cbfSimulationMode:
        print("Device is in simulation mode")
        return 1
    print("Device is not in simulation mode")
    return 0


def start_device(dev: tango.DeviceProxy) -> int:
    """
    Set up device connection and timeouts.

    :param dev: Tango device handle
    :return: error condition
    """
    log_prog(f"Turn on device {dev.name()}")
    dev.on()
    print(f"Status : {dev.Status()}")
    return 0


def start_ctl_device(dev: tango.DeviceProxy, subsystems: list) -> int:
    """
    Start a Tango device.

    :param dev: Tango device handle
    :param subsystems: list, usually empty
    :return: error condition
    """
    log_prog(f"Start control device {dev.name()} is ON")
    dev_state = dev.State()
    # pylint: disable-next=c-extension-no-member
    if dev_state == tango._tango.DevState.ON:
        print(f"Device {dev.name()} is ON")
    else:
        print(f"Device {dev.name()} is OFF")
    # Send the ON command
    print(f"Send on command to subsystems {subsystems}")
    # an empty list sends the ON command to ALL the subsystems, specific subsystems
    # are turned on if specified in a list of subsystem FQDNs
    dev.on(subsystems)
    dev_state = dev.State()
    print(f"Status : {dev.Status()}")
    # pylint: disable-next=c-extension-no-member
    if dev_state != tango._tango.DevState.ON:
        print("Device %s is not on" % dev.name())
        return 1
    return 0


def get_surrogate(
    ns_name: str, ns_sdp_name: str, databaseds_name: str
) -> Tuple[Any, Any | None]:
    """
    Control the CSP subarray.

    Set up a Tango DeviceProxy to the CSP Subarray device

    :param ns_name: Kubernetes namespace
    :param ns_sdp_name: Kubernetes namespace for SDP
    :param databaseds_name: database device server
    :return: error conition
    """
    k8s = KubernetesControl(_module_logger)
    # Get Tango database service
    svcs = k8s.get_services(ns_name, databaseds_name)
    for svc_nm in svcs:
        svc = svcs[svc_nm]
        svc_ns = svc[0]
        svc_ip = svc[1]
        svc_port = svc[2]
        svc_prot = svc[3]
        print(f"{svc_ip:<15}  {svc_port:<5}  {svc_prot:<8} {svc_ns:<64}  {svc_nm}")

    # Get surrogate receiver interface IP address
    pods = k8s.get_pods(ns_sdp_name, None)
    if len(pods) > 1:
        print("More than one pod in namespace %s" % ns_sdp_name)
    pod_ip = None
    pod_nm = None
    for pod_nm in pods:
        pod = pods[pod_nm]
        pod_ip = pod[0]
        print(f"{pod_nm}  {pod_ip}")
    if pod_ip is None:
        print("Could not read IP address in namespace %s" % ns_sdp_name)

    sdp_host_ip_address = pod_ip
    print(f"Surrogate receiver interface IP address {sdp_host_ip_address}")

    return pod_nm, sdp_host_ip_address


def init_subarray(sub_dev: tango.DeviceProxy, resources: Any) -> int:
    """
    Initialize subarray

    :param sub_dev: subarray Tango device
    :param resources: JSON data
    :return: error condition
    """
    log_prog(f"Initialize subarray device {sub_dev.name()}")
    print(f"Status : {sub_dev.Status()}")
    print(f"Resources {resources}")
    try:
        sub_dev.AssignResources(resources)
    except tango.DevFailed as e:
        print(f"Could not assign resources:\n{repr(e)}")
        return 1
    return 0


def control_subarray(
    sub_dev: tango.DeviceProxy, sdp_host_ip_address: Any | None
) -> int:
    """
    Control the CSP subarray.

    Set up a Tango DeviceProxy to the CSP Subarray device

    :param sub_dev: subarray Tango device handle
    :param sdp_host_ip_address: surrogate pod address
    :return: error conition
    """
    # pylint: disable-next=global-variable-not-assigned
    global CONFIGUREDATA

    log_prog(f"Control the CSP Subarray {sub_dev.name()}")
    print(f"Status : {sub_dev.Status()}")
    CONFIGUREDATA["cbf"]["fsp"][0]["output_host"] = sdp_host_ip_address

    # json_obj = json.loads(CONFIGUREDATA)
    # json_str = json.dumps(json_obj, indent=4)
    print("CONFIGURE DATA")
    pp = pprint.PrettyPrinter(depth=8)
    pp.pprint(CONFIGUREDATA)

    print(f"Control subarray {sub_dev.name()}")
    # sub_dev = tango.DeviceProxy(sub_name)
    resources = json.dumps({"subarray_id": 1, "dish": {"receptor_ids": ["SKA001"]}})
    sub_dev.AssignResources(resources)

    # subarray.ConfigureScan(json.dumps(CONFIGUREDATA))
    try:
        sub_dev.Configure(json.dumps(CONFIGUREDATA))
    except tango.DevFailed as e:
        print(f"Could not configure subarray: {repr(e)}")
        return 1

    return 0


def setup_bite_stream(ns_name: str, pod_name: str, exec_cmd: list) -> int:
    """
    Set up BITE data stream.

    kubectl -n integration exec ec-bite -- python3 midcbf_bite.py \
        --talon-bite-lstv-replay --boards=1

    :param ns_name: Kubernetes namespace
    :param pod_name: Kubernetes pod
    :param exec_cmd: command to execute
    :return: None
    """
    log_prog(f"Setup BITE data stream in pod {pod_name}")
    # kube_cmd = f"kubectl -n {ns_name} exec {pod_name} -- {' '.join(exec_cmd)}"
    print()
    k8s = KubernetesControl(_module_logger)
    print(f"Run> {' '.join(exec_cmd)}")
    k8s.exec_command(ns_name, pod_name, exec_cmd)
    return 0


def upload_delay(leaf_dev_name: str) -> int:
    """
    Upload the delay model.

    :param leaf_dev_name: Tango device name
    :return: error condition
    """
    log_prog("Upload the delay model")
    # Generate the Delaymodel and check if it was was correctly sent:\n",
    # ska_mid/tm_leaf_node/csp_subarray_01
    sub = tango.DeviceProxy(leaf_dev_name)
    print(f"Status : {sub.Status()}")
    current_time = float(
        datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).timestamp()
    )
    dm = {
        "interface": "https://schema.skao.int/ska-csp-delaymodel/2.2",
        "epoch": current_time,
        "validity_period": 400.0,
        "delay_details": [
            {
                "receptor": "SKA001",
                "poly_info": [
                    {"polarization": "X", "coeffs": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]},
                    {"polarization": "Y", "coeffs": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]},
                ],
            }
        ],
    }
    sub.delayModel = json.dumps(dm)
    if sub.delayModel != json.dumps(dm):
        print("Delay model not OK")
    print(f"Expected {dm}, got\n{sub.delayModel}")
    return 0


def scan_data(ns_name: str, pod_name: str) -> int:
    """
    Look at the output of tcpdump -i net1 in the SDP Surrogate pod and see data.

    :param ns_name: Kubernetes namespace
    :param pod_name: Kubernetes pod
    :return: None
    """
    log_prog(f"Check netword traffic in pod {pod_name}")
    k8s = KubernetesControl(_module_logger)
    scan_cmd = ["tcpdump", "-i", "net1", "-c", "10"]
    print(f"Run> {' '.join(scan_cmd)}")
    k8s.exec_command(ns_name, pod_name, scan_cmd)
    return 0


def csp_shutdown(subarray_dev: tango.DeviceProxy) -> int:
    """
    End Scan (CSP Subarray).

    :param subarray_dev: subarray Tango device
    :return: error condition
    """
    print(f"End scan on device {subarray_dev.name()}")
    print(f"Status : {subarray_dev.Status()}")
    try:
        subarray_dev.EndScan()
    except tango.DevFailed as dev_err:
        print("Could not end scan")
        # print(f"Error: {dev_err}")
    print("*** Go To Idle (CSP Subarray) ***")
    try:
        subarray_dev.GoToIdle()
    except tango.DevFailed:
        print("Could not go to idle")
    print(f"CSP obs state: {subarray_dev.obsState}")
    print("*** Release Resources (CSP Subarray) ***")
    try:
        subarray_dev.ReleaseAllResources()
    except tango.DevFailed:
        print("Could not release resources")
    print(f"Status : {subarray_dev.Status()}")
    return 0


def do_startup(
    ctl_dev_name: str,
    timeout: int,
    dev_sim: bool,
    show_status: bool,
    sub_dev_name: str,
    resource_data: str,
    long_cmds: int,
) -> Tuple[int, Any]:
    """
    Start up specified Tango devices.

    :param ctl_dev_name: control Tango device name
    :param timeout: in seconds
    :param show_status: flag to show status and return
    :param sub_dev_name: subarray Tango device name
    :param resource_data: resource data used to initialize device
    :param long_cmds: number of long-running commands to accept
    :return: error condition and handle for subarray Tango device
    """
    log_prog(f"Start up device {ctl_dev_name}")
    _rc, ctl_dev = setup_device(ctl_dev_name)
    if ctl_dev is None:
        print("Dould not create control Tango device %s", ctl_dev_name)
        return 1, None
    print(f"Status : {ctl_dev.Status()}")
    if not check_device(ctl_dev):
        print(f"Could not ping device {ctl_dev_name}")
        return 1, None
    print(f"Communication with device {ctl_dev_name} is OK")
    device_state(ctl_dev)
    if show_status:
        return 1, None

    init_device(ctl_dev, timeout, dev_sim)
    device_state(ctl_dev)
    show_long_running_command(ctl_dev)

    _rc, sub_dev = setup_device(sub_dev_name)
    if sub_dev is None:
        print("Dould not create subarray Tango device %s", sub_dev_name)
        return 1, None
    device_state(sub_dev)

    # assign resources
    encode_data = json.dumps(resource_data, indent=2).encode('utf-8')
    _rc = start_device(sub_dev)
    _rc = init_subarray(sub_dev, encode_data)
    lrc = show_long_running_command(sub_dev)
    l_count = 0
    while lrc > long_cmds:
        l_count += 1
        if l_count > 5:
            print(
                "Long running commands still active after"
                f" {(l_count*timeout)/60} minutes"
            )
            return 1, None
        print(f"Waiting for {lrc} long running commands")
        time.sleep(timeout)
        lrc = show_long_running_command(sub_dev)

    # an empty list sends the ON command to ALL the subsystems, specific subsystems
    # are turned on if specified in a list of subsystem FQDNs
    subsystems: List[Any] = []
    _rc = start_ctl_device(ctl_dev, subsystems)  # noqa: F841
    return 0, sub_dev


def do_control(
    sub_dev_name: str,
    sub_dev: Any,
    ns_name: str,
    databaseds_name: str,
    ns_sdp_name: str,
    leaf_dev_name: str,
    bite_cmd: List[str],
) -> int:
    """
    Control the thing.

    :param sub_dev_name: subarray Tango device name
    :param sub_dev: subarray Tango device
    :param ns_name: namespace name
    :param databaseds_name: Tango database
    :param ns_sdp_name: surrogate namespace
    :param leaf_dev_name: leaf Tango device name
    :param bite_cmd: command to do the BITE thing
    :return: error condition
    """
    # Get address for SDP surrogate pod
    sdp_pod_nm, sdp_host_ip_address = get_surrogate(
        ns_name, ns_sdp_name, databaseds_name
    )
    log_prog(f"Control subarray device {sub_dev_name}")
    if sub_dev is None:
        _rc, sub_dev = setup_device(sub_dev_name)
        if sub_dev is None:
            print("Dould not create subarray Tango device %s", sub_dev_name)
            return 1
    print(f"Status : {sub_dev.Status()}")

    rc = control_subarray(sub_dev, sdp_host_ip_address)
    if rc:
        print("Control subarray failed")
        return 1

    setup_bite_stream(ns_name, sdp_pod_nm, bite_cmd)

    upload_delay(leaf_dev_name)

    scan_data(ns_sdp_name, sdp_pod_nm)

    return 0


def do_shutdown(
    ctl_dev_name: str,
    sub_dev_name: str,
    tear_down: bool,
) -> int:
    """
    Start up specified Tango devices.

    :param ctl_dev_name: control Tango device name
    :param sub_dev_name: subarray Tango device name
    :param tear_down: shut down everything when done
    :return: error conition:

    """
    log_prog(f"Shut down device {sub_dev_name}")
    sub_dev = tango.DeviceProxy(sub_dev_name)
    csp_shutdown(sub_dev)
    print(f"Status : {sub_dev.Status()}")

    if tear_down:
        log_prog(f"Tear down device {ctl_dev_name}")
        ctl_dev = tango.DeviceProxy(ctl_dev_name)
        device_teardown(ctl_dev)
        print(f"Status : {ctl_dev.Status()}")

    return 0


def device_teardown(csp_dev: tango.DeviceProxy) -> int:
    """
    Turn off the (CSP and CBF) Tango device.

    This should only be done if you don't want to use the system again.

    :param csp_dev: CSP Tango device
    :return: error condition
    """
    print(f"Turn off device {csp_dev.name()}")
    # Check with make itf-cbf-talonlru-status - lru should be off now
    try:
        csp_dev.off([])
    except tango.DevFailed:
        print("Could not turn device off")
    print(f"Status : {csp_dev.Status()}")
    csp_dev.cbfSimulationMode = True
    csp_dev.commandTimeout = 3
    csp_dev.adminmode = 1
    print(f"Admin mode : {csp_dev.adminmode}")
    return 0


def usage(p_name: str, mid_sys: str, cfg_data: Any) -> None:
    """
    Show how it is done.

    :param p_name: executable name
    :param mid_sys: subsystem name
    :param cfg_data: configuration data
    """
    print("Start system:")
    print(
        f"\t{p_name} --start"
        " [--csp|--tmc] [--simul]"
        " [--jobs=<JOBS>]"
        " [--csp|--tmc]"
        " [--control=<DEVICE>]"
        " [--subarray=<DEVICE]"
        " [--leafnode=<LEAFNODE>]"
        " [--namespace=<NAMESPACE>]"
        " [--service=<SERVICE>]"
        " [--system=<SYSTEM>]"
    )
    print("Control system:")
    print(
        f"\t{p_name} --ctrl"
        " [--csp|--tmc]"
        " [--subarray=<DEVICE]"
        " [--namespace=<NAMESPACE>]"
        " [--leafnode=<LEAFNODE>]"
    )
    print("Stop system:")
    print(
        f"\t{p_name} --stop [--teardown]"
        " [--csp|--tmc]"
        " [--control=<DEVICE>]"
        " [--subarray=<DEVICE]"
    )
    print("Check Tango status:")
    print(f"\t{p_name} -t")
    print("Display observation state:")
    print(f"\t{p_name} --observation [--subarray=<DEVICE]")
    print("Display long running commands:")
    print(f"\t{p_name} --long-cmd [--subarray=<DEVICE]")
    print("where:")
    for mid_sys in ("csp", "tmc"):
        print(
            f"\t--{mid_sys}\tuse {get_ska_jargon(mid_sys)} subsystem:"
        )
        if mid_sys in ["csp"]:
            print(
                "\t\t--jobs=<JOBS>\t\tMinimum number of long running commands,"
                f" default for {mid_sys.upper()}"
                f" is {cfg_data[mid_sys]['long_run_cmds']}"
            )
        print(
            "\t\t--control=<DEVICE>\tTango control device,"
            f"default for {mid_sys.upper()} is {cfg_data[mid_sys]['control_device']}"
        )
        print(
            "\t\t--subarray=<DEVICE>\tTango subarray device,"
            f"default for {mid_sys.upper()} is {cfg_data[mid_sys]['subarray_device']}"
        )
        print(
            "\t\t--leafnode=<LEAFNODE>\tTango leafnode device,"
            f" default for {mid_sys.upper()} is {cfg_data[mid_sys]['leafnode_device']}"
        )
    print(f"\t--simul\t\t\tsimulate {get_ska_jargon('CBF')}")
    print(
        "\t--namespace=<NAMESPACE>\tKubernetes namespace,"
        f" default is {cfg_data['kube_namespace']}"
    )
    print(
        "\t--service=<SERVICE>\tKubernetes service for Tango database,"
        f" default is {cfg_data['databaseds_name']}"
    )
    print("\t--teardown\t\tTear down control device at the end")


def main(y_arg: list) -> int:  # noqa: C901
    """
    Start Tango devices for MID ITF.

    :param y_arg: input arguments
    """
    cfg_data = read_config_json(f"{os.path.dirname(y_arg[0])}/mid_startup.json")

    ns_name: str = cfg_data["kube_namespace"]
    svc_name: str = cfg_data["databaseds_name"]
    cluster_domain: str = cfg_data["cluster_domain"]
    databaseds_name: str = cfg_data["databaseds_name"]
    timeout = cfg_data["timeout"]
    mid_sys = ""
    sub_dev: Any = None
    ctl_dev_name: str = ""
    sub_dev_name: str = ""
    leaf_dev_name: str = ""
    resource_data: str = ""
    long_cmds: int = -1
    bite_cmd: List[str] = []
    # TODO read JSON data from file
    _resource_file: str | None = None  # noqa: F841
    show_tango: bool = False
    show_status: bool = False
    tear_down = False
    show_cfg = False
    show_obs = False
    show_long = False
    dev_start = False
    dev_ctrl = False
    dev_stop = False
    dev_sim = False

    try:
        opts, _args = getopt.getopt(
            y_arg[1:],
            "acdefhlopstvVC:D:J:L:N:R:S:",
            [
                "help",
                "csp",
                "tmc",
                "config",
                "long-cmd",
                "observation",
                "sim",
                "start",
                "control",
                "stop",
                "teardown",
                "status",
                "jobs=",
                "namespace=",
                "service=",
                "control=",
                "subarray=",
                "leafnode=",
                "resource=",
            ],
        )  # noqa: F841
    except getopt.GetoptError as opt_err:
        print(f"Could not read command line: {opt_err}")
        return 1

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(os.path.basename(y_arg[0]), mid_sys, cfg_data)
            sys.exit(1)
        elif opt in ("-C", "--control"):
            ctl_dev_name = arg
        elif opt in ("-D", "--subarray"):
            sub_dev_name = arg
        elif opt in ("-J", "--jobs"):
            long_cmds = int(arg)
        elif opt in ("-L", "--leafnode"):
            leaf_dev_name = arg
        elif opt in ("-N", "--namespace"):
            ns_name = arg
        elif opt in ("-S", "--service"):
            svc_name = arg
        elif opt in ("-c", "--config"):
            show_cfg = True
        elif opt == "--sim":
            dev_sim = True
        elif opt == "--start":
            dev_start = True
        elif opt == "--ctrl":
            dev_ctrl = True
        elif opt == "--stop":
            dev_stop = True
        elif opt in ("-d", "--teardown"):
            tear_down = True
        elif opt in ("-a", "--status"):
            show_status = True
        elif opt in ("-l", "--long-cmd"):
            show_long = True
        elif opt in ("-o", "--observation"):
            show_obs = True
        elif opt == "--csp":
            mid_sys = "csp"
        elif opt == "--tmc":
            mid_sys = "tmc"
        elif opt == "-t":
            show_tango = True
        elif opt == "-v":
            ska_ser_logging.configure_logging(logging.INFO)
            _module_logger.setLevel(logging.INFO)
        elif opt == "-V":
            ska_ser_logging.configure_logging(logging.DEBUG)
            _module_logger.setLevel(logging.DEBUG)
        else:
            print("Invalid option %s" % opt)

    if not mid_sys:
        print("System must be specified, use --csp or --tmc")
        return 1

    if not ctl_dev_name:
        ctl_dev_name = cfg_data[mid_sys]["control_device"]
    if not sub_dev_name:
        sub_dev_name = cfg_data[mid_sys]["subarray_device"]
    if not leaf_dev_name:
        leaf_dev_name = cfg_data[mid_sys]["leafnode_device"]
    if not resource_data:
        resource_data = cfg_data[mid_sys]["subarray_resources"]
    if not long_cmds < 0:
        long_cmds = int(cfg_data[mid_sys]["long_run_cmds"])
    if not bite_cmd:
        bite_cmd = cfg_data[mid_sys]["bite_cmd"]

    show_config_json(mid_sys, cfg_data)
    if show_cfg:
        return 1

    ns_sdp_name = f"{ns_name}-sdp"

    # Set the Tango host
    tango_fqdn = f"{svc_name}.{ns_name}.svc.{cluster_domain}"
    # print("Tango database FQDN is %s" % tango_fqdn)
    tango_port = 10000
    tango_host = f"{tango_fqdn}:{tango_port}"
    # print("Tango host %s" % tango_host)
    os.environ["TANGO_HOST"] = tango_host

    rc = check_tango(tango_fqdn, tango_port)
    if rc or show_tango:
        return 1
    progrs = 0
    if show_obs:
        rc = show_observation_status(sub_dev_name)
        progrs += 1
    if show_long:
        rc = show_long_running_commands(sub_dev_name)
        progrs += 1

    # Start Tango devices
    if dev_start:
        rc, sub_dev = do_startup(
            ctl_dev_name,
            timeout,
            dev_sim,
            show_status,
            sub_dev_name,
            resource_data,
            long_cmds,
        )
        progrs += 1
    # Control Tango devices
    if dev_ctrl:
        rc = do_control(
            sub_dev_name,
            sub_dev,
            ns_name,
            databaseds_name,
            ns_sdp_name,
            leaf_dev_name,
            bite_cmd,
        )
        progrs += 1
    # Stop Tango devices
    if dev_stop:
        rc = do_shutdown(
            ctl_dev_name,
            sub_dev_name,
            tear_down,
        )
        progrs += 1

    if not progrs:
        print("Nothing to do")
        print(f"Run '{os.path.basename(y_arg[0])} --help'")
        rc = 1

    return rc


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
