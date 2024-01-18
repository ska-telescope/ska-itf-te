#!/usr/bin/python
import getopt
import logging
import os
import socket
import sys
import tango
import time
import datetime
import json
from tango import DeviceProxy, Database
from kubernetes import client, config
from ska_control_model import AdminMode

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
TIMEOUT = 60


def get_k8s_service(isvc, ns_name: str | None, svc_name: str | None):
    isvc_ns = isvc.metadata.namespace
    if ns_name is not None:
        if isvc_ns != ns_name:
            _module_logger.debug("Skip namespace %s", isvc_ns)
            return
    isvc_name = isvc.metadata.name
    if svc_name is not None:
        if svc_name != isvc_name:
            _module_logger.debug("Skip service %s", isvc_name)
            return
    _module_logger.debug("Service %s:\n%s", isvc_name, isvc)
    try:
        svc_ip = isvc.status.load_balancer.ingress[0].ip
        svc_port = str(isvc.spec.ports[0].port)
        svc_prot = isvc.spec.ports[0].protocol
    except TypeError:
        svc_ip = "---"
        svc_port = ""
        svc_prot = ""
    return isvc_name, isvc_ns, svc_ip, svc_port, svc_prot


def get_k8s_tangodb(ns_name: str, svc_name: str):
    """
    Read IP address and port for a service (e.g. Tango database) from Kubernetes cluster

    :param v1: k8s handle
    :param svc_name: service name
    :return: none
    """
    config.load_kube_config()
    v1 = client.CoreV1Api()
    if svc_name:
        print(f"Service {svc_name}", end="")
    else:
        print("Services", end="")
    if ns_name:
        print(f" in namespace {ns_name}", end="")
    print()
    services = v1.list_service_for_all_namespaces(watch=False)
    _module_logger.info("Read %d services", len(services.items))
    for isvc in services.items:
        try:
            svc_name, svc_ns, svc_ip, svc_port, svc_prot = get_k8s_service(isvc, ns_name, svc_name)
            print(f"{svc_ip:<15}  {svc_port:<5}  {svc_prot:<8} {svc_ns:<64}  {svc_name}")
        except TypeError:
            pass


def get_tango_admin(dev) -> bool:
    csp_admin = dev.adminMode
    if csp_admin == AdminMode.ONLINE:
        print("Device admin mode online")
        return True
    if csp_admin == AdminMode.OFFLINE:
        print("Device admin mode offline")
    else:
        print(f"Device admin mode {csp_admin}")
    return False


def set_tango_admin(dev, dev_adm: bool, sleeptime: int = 2):
    if dev_adm:
        dev.adminMode = AdminMode.ONLINE
    else:
        dev.adminMode = AdminMode.OFFLINE
    time.sleep(sleeptime)
    return get_tango_admin(dev)


def usage(p_name: str) -> None:
    """
    Show how it is done.

    :param p_name: executable name
    """
    print("Display namespaces")
    print(f"\t{p_name} -n")


def main(y_arg: list) -> int:
    """
    Read and display Tango devices.

    :param y_arg: input arguments
    """
    ns_name: str | None = None
    svc_name: str | None = None
    dev_name: str = "mid-csp/control/0"

    try:
        opts, _args = getopt.getopt(
            y_arg[1:],
            "efhnpsvVD:N:S:",
            ["help", "namespace=", "service=", "device="],
        )
    except getopt.GetoptError as opt_err:
        print(f"Could not read command line: {opt_err}")
        return 1

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(os.path.basename(y_arg[0]))
            sys.exit(1)
        elif opt in ("-D", "--device"):
            dev_name = arg
        elif opt in ("-N", "--namespace"):
            ns_name = arg
        elif opt in ("-S", "--service"):
            svc_name = arg
        elif opt == "-v":
            _module_logger.setLevel(logging.INFO)
        elif opt == "-V":
            _module_logger.setLevel(logging.DEBUG)
        else:
            _module_logger.error("Invalid option %s", opt)

    if ns_name is None:
        ns_name = KUBE_NAMESPACE
    if svc_name is None:
        svc_name = DATABASEDS_NAME

    tango_fqdn = f"{svc_name}.{ns_name}.svc.{CLUSTER_DOMAIN}"
    _module_logger.info("Tango database FQDN is %s", tango_fqdn)
    tango_port = 10000
    tango_host = f"{tango_fqdn}:{tango_port}"
    print("Tango host %s" % tango_host)

    # finally set the TANGO_HOST
    os.environ["TANGO_HOST"] = tango_host

    try:
        addr1 = socket.gethostbyname_ex(tango_fqdn)
        tango_ip = addr1[2][0]
    except socket.gaierror as e:
        _module_logger.error("Could not read address %s : %s", addr1, e)
        return 1
    print(f"Tango host address {tango_ip}")

    get_k8s_tangodb(ns_name, DATABASEDS_NAME)

    print(f"Tango device : {dev_name}")
    csp = tango.DeviceProxy(dev_name)
    csp_admin = get_tango_admin(csp)
    print(f"Device status : {csp.Status()}")
    csp_state = csp.State()
    print(f"Device state : {csp_state}")
    if csp_state != tango._tango.DevState.ON:
        _module_logger.warning("Device %s is off", dev_name)
        csp_admin = set_tango_admin(csp, False)
        csp_state = csp.State()
        if csp_state != tango._tango.DevState.ON:
            _module_logger.error("Device %s is off", dev_name)
            return 1
    csp.commandTimeout = TIMEOUT
    if not csp.cbfSimulationMode:
        _module_logger.error("Device is not in simulation mode", dev_name)
        return 1
    csp_admin = set_tango_admin(csp, True)
    csp_state = csp.State()
    if csp_state != tango._tango.DevState.OFF:
        _module_logger.error("Device %s is on", dev_name)
        return 1
    return 0


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
