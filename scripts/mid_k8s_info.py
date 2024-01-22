#!/usr/bin/python
import getopt
import logging
import os
import sys

from k8s_ctl.get_k8s_info import KubernetesControl

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger(__name__)
_module_logger.setLevel(logging.WARNING)


def usage(p_name: str) -> None:
    """
    Show how it is done.

    :param p_name: executable name
    """
    print("Display namespaces")
    print(f"\t{p_name} -n [--namespace=<NAMESPACE>]")
    print("Display pods")
    print(f"\t{p_name} -p [--namespace=<NAMESPACE>] [--pod=<POD>]")
    print("Display services")
    print(f"\t{p_name} -s [--namespace=<NAMESPACE>] [--service=<SERVICE>]")
    print("where:")
    print("\t--namespace=<NAMESPACE>\tfilter by namespace")
    print("\t--pod=<POD>\t\tfilter by pod name")
    print("\t--service=<SERVICE>\tfilter by service name")


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
            "hnpsvVN:P:S:",
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
        elif opt == "-s":
            show_svc = True
        elif opt == "-v":
            _module_logger.setLevel(logging.INFO)
        elif opt == "-V":
            _module_logger.setLevel(logging.DEBUG)
        else:
            _module_logger.error("Invalid option %s", opt)

    k8s = KubernetesControl(_module_logger)
    if show_ns:
        print("Namespaces:")
        ns_list = k8s.get_namespaces()
        for ns_name in ns_list:
            print(f"{ns_name}")
    if show_pod:
        if pod_name:
            print(f"Pod {pod_name}", end="")
        else:
            print("Pods", end="")
        if ns_name:
            print(f" in namespace {ns_name}", end="")
        print()
        ipods = k8s.get_pods(ns_name, pod_name)
        for pod_nm in ipods:
            pod_ip = ipods[pod_nm][0]
            pod_ns = ipods[pod_nm][1]
            if pod_ns is None:
                pod_ns = "---"
            print(f"{pod_ip:<15}", end="")
            print(f"  {pod_ns:<64}", end="")
            print(f"  {pod_nm}")
    if show_svc:
        if svc_name:
            print(f"Service {svc_name}", end="")
        else:
            print("Services", end="")
        if ns_name:
            print(f" in namespace {ns_name}", end="")
        print()
        svcs = k8s.get_services(ns_name, svc_name)
        for svc_name in svcs:
            svc = svcs[svc_name]
            svc_ns = svc[0]
            svc_ip = svc[1]
            svc_port = svc[2]
            svc_prot = svc[3]
            print(f"{svc_ip:<15}  {svc_port:<5}  {svc_prot:<8} {svc_ns:<64}  {svc_name}")
    return 0


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
