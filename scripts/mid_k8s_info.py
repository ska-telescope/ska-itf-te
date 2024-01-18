#!/usr/bin/python
import getopt
import logging
import os
import sys
from kubernetes import client, config

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger(__name__)
_module_logger.setLevel(logging.WARNING)


def get_k8s_namespaces(v1):
    # config.load_kube_config()
    # v1 = client.CoreV1Api()
    namespaces = v1.list_namespace()
    _module_logger.debug("Namespaces: %s", namespaces)
    print("Namespaces:")
    for namespace in namespaces.items:
        _module_logger.debug("Namespace: %s", namespace)
        ns_name = namespace.metadata.name
        print(f"{ns_name}")


def get_k8s_pod(ipod, ns_name: str | None, pod_name: str | None):
    i_ns_name = ipod.metadata.namespace
    if ns_name is not None:
        if i_ns_name != ns_name:
            return
    i_pod_name = ipod.metadata.name
    if pod_name is not None:
        if i_pod_name != pod_name:
            return
    i_pod_ip = ipod.status.pod_ip
    if i_pod_ip is None:
        i_pod_ip = "---"
    _module_logger.debug("Pod %s:\n%s", i_ns_name, ipod)
    print(f"{i_pod_ip:<15}", end="")
    print(f"  {i_ns_name:<64}", end="")
    print(f"  {i_pod_name}")


def get_k8s_pods(v1, ns_name: str | None, pod_name: str | None):
    # Configs can be set in Configuration class directly or using helper utility
    # config.load_kube_config()
    #
    # v1 = client.CoreV1Api()
    _module_logger.info("Listing pods with their IPs for namespace %s", ns_name)
    if pod_name:
        print(f"Pod {pod_name}", end="")
    else:
        print("Pods", end="")
    if ns_name:
        print(f" in namespace {ns_name}", end="")
    print()
    ret = v1.list_pod_for_all_namespaces(watch=False)
    for ipod in ret.items:
        get_k8s_pod(ipod, ns_name, pod_name)


def get_k8s_service(isvc, ns_name: str | None, svc_name: str | None):
    isvc_name = isvc.metadata.name
    if svc_name is not None:
        if svc_name != isvc_name:
            return
    isvc_ns = isvc.metadata.namespace
    if ns_name is not None:
        if isvc_ns != ns_name:
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
    print(f"{svc_ip:<15}  {svc_port:<5}  {svc_prot:<8} {isvc_ns:<64}  {isvc_name}")
    return isvc_name, isvc_ns, svc_ip, svc_port, svc_prot


def get_k8s_services(v1, ns_name: str | None, svc_name: str | None):
    """
        $ kubectl --namespace integration get service tango-databaseds -o json | jq -r .status.loadBalancer.ingress[].ip
    10.164.10.5
        $ kubectl --namespace integration get service tango-databaseds -o json | jq -r '.spec.ports[0]["port"]?'
    10000
        :param v1: k8s handle
        :param svc_name: service name
        :return:
    """
    if svc_name:
        print(f"Service {svc_name}", end="")
    else:
        print("Services", end="")
    if ns_name:
        print(f" in namespace {ns_name}", end="")
    print()
    services = v1.list_service_for_all_namespaces(watch=False)
    for isvc in services.items:
        get_k8s_service(isvc, ns_name, svc_name)


def usage(p_name: str) -> None:
    """
    Show how it is done.

    :param p_name: executable name
    """
    print("Display namespaces")
    print(f"\t{p_name} -n")
    print("Display pods")
    print(f"\t{p_name} -p")


def main(y_arg: list) -> int:
    ns_name: str | None = None
    svc_name: str | None = None
    pod_name: str | None = None
    show_ns: bool = False
    show_pod: bool = False
    show_svc: bool = False
    try:
        opts, _args = getopt.getopt(
            y_arg[1:],
            "efhnpsvVN:P:S:",
            ["help", "namespace=", "pod=", "service="],
        )
    except getopt.GetoptError as opt_err:
        print(f"Could not read command line: {opt_err}")
        return 1

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(os.path.basename(y_arg[0]))
            sys.exit(1)
        elif opt in ("-N", "--namespace"):
            ns_name = arg
        elif opt in ("-P", "--pod"):
            pod_name = arg
        elif opt in ("-S", "--service"):
            svc_name = arg
        elif opt == "-n":
            show_ns = True
        elif opt == "-p":
            show_pod = True
        # elif opt == "-f":
        #     fforce = True
        elif opt == "-s":
            show_svc = True
        elif opt == "-v":
            _module_logger.setLevel(logging.INFO)
        elif opt == "-V":
            _module_logger.setLevel(logging.DEBUG)
        else:
            _module_logger.error("Invalid option %s", opt)

    config.load_kube_config()
    v1 = client.CoreV1Api()
    if show_ns:
        get_k8s_namespaces(v1)
    if show_pod:
        get_k8s_pods(v1, ns_name, pod_name)
    if show_svc:
        get_k8s_services(v1, ns_name, svc_name)
    return 0


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
