#!/usr/bin/python
import datetime
import getopt
import json
import logging
import os
import pprint
import socket
import sys
import tango
import time
from typing import Any, Tuple

from ska_control_model import AdminMode

from k8s_ctl.get_k8s_info import KubernetesControl

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger(__name__)
_module_logger.setLevel(logging.WARNING)

# Take the namespace name from the deployment job
KUBE_NAMESPACE = "ci-ska-mid-itf-at-1820-tmc-test-sdp-notebook-v2"
# KUBE_NAMESPACE = "integration"
# KUBE_NAMESPACE_SDP = "integration-sdp"
CLUSTER_DOMAIN = "miditf.internal.skao.int"
# set the name of the databaseds service
DATABASEDS_NAME = "tango-databaseds"
CONTROL_DEVICE = "mid-csp/control/0"
SUBARRAY_DEVICE = "mid-csp/subarray/01"
LEAFNODE_DEVICE = "ska_mid/tm_leaf_node/csp_subarray_01"
BITE_POD = "ec-bite"
BITE_CMD = ["python3", "midcbf_bite.py", "--talon-bite-lstv-replay", "--boards=1"]
TIMEOUT = 60

CONFIGUREDATA = {
    "interface": "https://schema.skao.int/ska-csp-configure/2.3",
    "subarray": {
        "subarray_name": "Single receptor"
    },
    "common": {
        "config_id": "1 receptor, band 1, 1 FSP, no options",
        "frequency_band": "1",
        "subarray_id": 0
    },
    "cbf": {
        "delay_model_subscription_point": "ska_mid/tm_leaf_node/csp_subarray_01/delayModel",
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
                    [0, 4], [744, 8], [1488, 12], [2232, 16], [2976, 20],
                    [3720, 24], [4464, 28], [5206, 32], [5952, 36], [6696, 40],
                    [7440, 44], [8184, 48], [8928, 52], [9672, 56], [10416, 60],
                    [11160, 64], [11904, 68], [12648, 72], [13392, 76], [14136, 80]
                ],
                "output_host": [
                    [0, "10.165.20.31"]
                ],
                "output_port": [
                    [0, 14000, 1]
                ]
            }
        ]
    }
}


def check_tango(tango_fqdn: str) -> int:
    """
    Check Tango host address.

    :param tango_fqdn:
    :return: error condition
    """
    try:
        tango_addr = socket.gethostbyname_ex(tango_fqdn)
        tango_ip = tango_addr[2][0]
    except socket.gaierror as e:
        _module_logger.error("Could not read address %s : %s", tango_fqdn, e)
        return 1
    print(f"Tango host address {tango_ip}")
    return 0


def get_tango_admin(dev: Any) -> bool:
    """
    Read admin mode for a Tango device.

    :param dev: Tango device handle
    :return: True when device is in admin mode
    """
    csp_admin = dev.adminMode
    if csp_admin == AdminMode.ONLINE:
        print("Device admin mode online")
        return True
    if csp_admin == AdminMode.OFFLINE:
        print("Device admin mode offline")
    else:
        print(f"Device admin mode {csp_admin}")
    return False


def setup_device(dev_name: str) -> Tuple[int, Any]:
    """
    Set up device connection and timeouts.

    :param dev_name: Tango device name
    :return: None
    """
    print("*** Setup Device connection and Timeouts ***")
    print(f"Tango device : {dev_name}")
    dev = tango.DeviceProxy(dev_name)
    # check AdminMode
    csp_admin = get_tango_admin(dev)
    print(f"Device status : {dev.Status()}")
    csp_state = dev.State()
    print(f"Device state : {csp_state}")
    # Set Adminmode to ONLINE and check state
    if csp_state != tango._tango.DevState.ON:
        _module_logger.warning("Device %s is off", dev_name)
        csp_admin = set_tango_admin(dev, False)
        csp_state = dev.State()
        if csp_state != tango._tango.DevState.ON:
            _module_logger.error("Device %s is off", dev_name)
            return 1, dev
    # Set Timeout to 60 seconds as the ON command is a long-running command
    dev.commandTimeout = TIMEOUT
    # check value
    print(f"Command timeout is {dev.commandTimeout}")
    # Check CBF SimulationMode (this should be FALSE for real hardware control)
    if not dev.cbfSimulationMode:
        _module_logger.error("Device is not in simulation mode", dev_name)
        return 1, dev
    return 0, dev


def start_device(dev, subsystems: list, dry_run: bool) -> int:
    """
    Start a Tango device.

    :param dev: Tango device handle
    :param subsystems: list, usually empty
    :param dry_run: dry run flag
    :return: error condition
    """
    dev_state = dev.State()
    if dev_state == tango._tango.DevState.ON:
        print(f"Device {dev.name()} is ON")
    else:
        print(f"Device {dev.name()} is OFF")
    # Send the ON command
    print(f"Send on command to subsystems {subsystems}")
    if dry_run:
        print("Dry run")
        return 0
    # an empty list sends the ON command to ALL the subsystems, specific subsystems
    # are turned on if specified in a list of subsystem FQDNs
    dev.on(subsystems)
    dev_state = dev.State()
    if dev_state != tango._tango.DevState.ON:
        _module_logger.error("Device %s is not on", dev.name())
        return 1
    return 0


def get_surrogate(ns_name: str, ns_sdp_name: str, dry_run: bool) -> Tuple[str, str]:
    """
    Control the CSP subarray.

    Set up a Tango DeviceProxy to the CSP Subarray device

    :param ns_name: Kubernetes namespace
    :param ns_sdp_name: Kubernetes namespace for SDP
    :param dry_run: dry run flag
    :return: error conition
    """
    k8s = KubernetesControl(_module_logger)
    # Get Tango database service
    svcs = k8s.get_services(ns_name, DATABASEDS_NAME)
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
        _module_logger.warning("More than one pod in namespace %s", ns_sdp_name)
    pod_ip = None
    for pod_nm in pods:
        pod = pods[pod_nm]
        pod_ip = pod[0]
        print(f"{pod_nm}  {pod_ip}")
    if pod_ip is None:
        _module_logger.error("Could not read IP address in namespace %s", ns_sdp_name)

    sdp_host_ip_address = pod_ip
    print(f"Surrogate receiver interface IP address {sdp_host_ip_address}")

    return pod_nm, sdp_host_ip_address


def control_subarray(sdp_host_ip_address: str, sub_name: str, dry_run: bool) -> Any:
    """
    Control the CSP subarray.

    Set up a Tango DeviceProxy to the CSP Subarray device

    :param sub_name: subarray Tango device name
    :param sdp_host_ip_address: surrogate pod address
    :param dry_run: dry run flag
    :return: error conition
    """
    global CONFIGUREDATA

    print("*** Control the CSP Subarray ***")
    CONFIGUREDATA["cbf"]["fsp"][0]["output_host"] = sdp_host_ip_address

    # json_obj = json.loads(CONFIGUREDATA)
    # json_str = json.dumps(json_obj, indent=4)
    print("CONFIGURE DATA")
    pp = pprint.PrettyPrinter(depth=8)
    pp.pprint(CONFIGUREDATA)

    if dry_run:
        print("Dry run")
        return 0

    print("Control subarray {sub_name}")
    subarray = tango.DeviceProxy(sub_name)
    resources = json.dumps({
        "subarray_id": 1,
        "dish":{
            "receptor_ids":["SKA001"]
        }
    })
    subarray.AssignResources(resources)

    subarray.ConfigureScan(json.dumps(CONFIGUREDATA))

    return subarray


def setup_bite_stream(ns_name: str, pod_name: str, dry_run: bool, exec_cmd: list):
    """
    Set up BITE data stream.

    kubectl -n integration exec ec-bite -- python3 midcbf_bite.py \
        --talon-bite-lstv-replay --boards=1

    :param ns_name: Kubernetes namespace
    :param pod_name: Kubernetes pod
    :param dry_run: dry run flag
    :param exec_cmd: command to execute
    :return: None
    """
    print("*** Setup BITE data stream ***")
    kube_cmd = f"kubectl -n {ns_name} exec {pod_name} -- {' '.join(exec_cmd)}"
    print()
    k8s = KubernetesControl(_module_logger)
    print(f"Run> {' '.join(exec_cmd)}")
    if dry_run:
        return
    k8s.exec_command(ns_name, pod_name, exec_cmd)


def set_tango_admin(dev: Any, dev_adm: bool, sleeptime: int = 2) -> bool:
    """
    Write admin mode for a Tango device.

    :param dev: Tango device
    :param dev_adm: admin mode flag
    :param sleeptime: seconds to sleep
    :return: True when device is in admin mode
    """
    print("*** Set Adminmode to ONLINE and check state ***")
    if dev_adm:
        dev.adminMode = AdminMode.ONLINE
    else:
        dev.adminMode = AdminMode.OFFLINE
    time.sleep(sleeptime)
    return get_tango_admin(dev)


def upload_delay(leaf_dev_name: str, dry_run: bool):
    """
    Upload the delay model.

    :param leaf_dev_name: Tango device name
    :param dry_run: dry run flag
    :return: None
    """
    print("*** Upload the Delay model ***")
    # Generate the Delaymodel and check if it was was correctly sent:\n",
    # ska_mid/tm_leaf_node/csp_subarray_01
    sub = tango.DeviceProxy(leaf_dev_name)
    current_time = float(datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).timestamp())
    dm = {
        "interface": "https://schema.skao.int/ska-csp-delaymodel/2.2",
        "epoch": current_time,
        "validity_period": 400.0,
        "delay_details": [
            {
                "receptor": "SKA001", "poly_info": [
                    {
                        "polarization": "X",
                        "coeffs": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                    },
                    {
                        "polarization": "Y",
                        "coeffs": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                    }
                ]
            }
        ]
    }
    sub.delayModel = json.dumps(dm)
    if sub.delayModel != json.dumps(dm):
        _module_logger.error("Delay model not OK")
    print(f"Expected {dm}, got\n{sub.delayModel}")


def scan_data(ns_name: str, pod_name: str, dry_run: bool):
    """
    Look at the output of tcpdump -i net1 in the SDP Surrogate pod and see data.

    :param ns_name: Kubernetes namespace
    :param pod_name: Kubernetes pod
    :param dry_run: dry run flag
    :return: None
    """
    k8s = KubernetesControl(_module_logger)
    scan_cmd = ["tcpdump", "-i", "net1", "-c", "10"]
    print(f"Run> {' '.join(scan_cmd)}")
    if dry_run:
        return
    k8s.exec_command(ns_name, pod_name, scan_cmd)


def csp_shutdown(subarray_dev: Any):
    """
    End Scan (CSP Subarray).

    :param subarray_dev: subarray Tango device
    :return: None
    """
    print(f"End scan on device {subarray_dev.name()}")
    subarray_dev.EndScan()
    print("*** Go To Idle (CSP Subarray) ***",
          subarray_dev.GoToIdle()
    print(f"CSP obs state: {subarray_dev.obsState}")
    print("*** Release Resources (CSP Subarray) ***")
    subarray_dev.ReleaseAllResources()


def csp_teardown(csp_dev: Any):
    """
    Turn off the CSP and CBF.

    :param csp_dev: CSP Tango device
    This should only be done if you don't want to use the system again."
    """
    print(f"Shut down device {csp_dev.name()}")
    print("*** Final Teardown ***")
    # Check with make itf-cbf-talonlru-status - lru should be off now
    csp_dev.off([])
    csp_dev.cbfSimulationMode = True
    csp_dev.commandTimeout = 3
    csp_dev.adminmode = 1


def usage(p_name: str) -> None:
    """
    Show how it is done.

    :param p_name: executable name
    """
    print("Display namespaces")
    print(
        f"\t{p_name}"
        " [--control=<DEVICE>]"
        " [--subarray=<DEVICE]"
        " [--leafnode=<LEAFNODE>]"
        " [--namespace=<NAMESPACE>]"
        " [--service=<SERVICE>]"
    )
    print("where:")
    print(f"\t--control=<DEVICE>\tTango control device, default is {CONTROL_DEVICE}")
    print(f"\t--subarray=<DEVICE>\tTango subarray device, default is {SUBARRAY_DEVICE}")
    print(
        f"\t--leafnode=<LEAFNODE>\tTango leafnode device, default is {LEAFNODE_DEVICE}"
    )
    print(
        f"\t--namespace=<NAMESPACE>\tKubernetes namespace, default is {KUBE_NAMESPACE}"
    )
    print(f"\t--service=<SERVICE>\tdatabase Tango device, default is {DATABASEDS_NAME}")


def main(y_arg: list) -> int:
    """
    Start Tango devices for MID ITF.

    :param y_arg: input arguments
    """
    ns_name: str = KUBE_NAMESPACE
    svc_name: str = DATABASEDS_NAME
    ctl_dev_name: str = CONTROL_DEVICE
    sub_dev_name: str = SUBARRAY_DEVICE
    leaf_dev_name: str = LEAFNODE_DEVICE
    show_tango: bool = False
    dry_run = False
    tear_down = False

    try:
        opts, _args = getopt.getopt(
            y_arg[1:],
            "defhnpstvVC:D:L:N:S:",
            [
                "help",
                "dry-run",
                "shutdown",
                "namespace=",
                "service=",
                "control=",
                "subarray=",
                "leafnode=",
            ],
        )
    except getopt.GetoptError as opt_err:
        print(f"Could not read command line: {opt_err}")
        return 1

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(os.path.basename(y_arg[0]))
            sys.exit(1)
        elif opt in ("-C", "--control"):
            ctl_dev_name = arg
        elif opt in ("-D", "--subarray"):
            sub_dev_name = arg
        elif opt in ("-L", "--leafnode"):
            leaf_dev_name = arg
        elif opt in ("-N", "--namespace"):
            ns_name = arg
        elif opt in ("-S", "--service"):
            svc_name = arg
        elif opt in ("-n", "--dry-run"):
            dry_run = True
        elif opt in ("-d", "--shutdown"):
            tear_down = True
        elif opt == "-t":
            show_tango = True
        elif opt == "-v":
            _module_logger.setLevel(logging.INFO)
        elif opt == "-V":
            _module_logger.setLevel(logging.DEBUG)
        else:
            _module_logger.error("Invalid option %s", opt)

    ns_sdp_name = f"{ns_name}-sdp"

    # Set the Tango host
    tango_fqdn = f"{svc_name}.{ns_name}.svc.{CLUSTER_DOMAIN}"
    _module_logger.info("Tango database FQDN is %s", tango_fqdn)
    tango_port = 10000
    tango_host = f"{tango_fqdn}:{tango_port}"
    print("Tango host %s" % tango_host)
    os.environ["TANGO_HOST"] = tango_host

    rc = check_tango(tango_fqdn)
    if rc or show_tango:
        return 1

    rc, ctl_dev = setup_device(ctl_dev_name)
    # an empty list sends the ON command to ALL the subsystems, specific subsystems
    # are turned on if specified in a list of subsystem FQDNs
    subsystems = []
    rc = start_device(ctl_dev, subsystems, dry_run)

    sdp_pod_nm, sdp_host_ip_address = get_surrogate(ns_name, ns_sdp_name, dry_run)

    sub_dev = control_subarray(sdp_host_ip_address, sub_dev_name, dry_run)

    setup_bite_stream(ns_name, dry_run)

    upload_delay(leaf_dev_name, dry_run)

    scan_data(ns_sdp_name, sdp_pod_nm)

    csp_shutdown(sub_dev)

    if tear_down:
        csp_teardown(ctl_dev)

    return 0


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
