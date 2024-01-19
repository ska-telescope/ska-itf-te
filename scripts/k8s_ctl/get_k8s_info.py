"""
Doing all sorts of K8S stuff.
"""
import logging
from kubernetes import client, config
import time

from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream


class KubernetesControl():
    """Do weird and wonderful things in a Kubernetes cluser."""

    v1 = None
    logger: logging.Logger | None = None

    def __init__(self, logger):
        """
        Get Kubernetes client

        :return: client handle
        """
        self.logger = logger
        self.logger.info("Get Kubernetes client")
        config.load_kube_config()
        self.v1 = client.CoreV1Api()

    def get_namespaces(self):
        # config.load_kube_config()
        # v1 = client.CoreV1Api()
        namespaces = self.v1.list_namespace()
        self.logger.debug("Namespaces: %s", namespaces)
        ns_list = []
        for namespace in namespaces.items:
            self.logger.debug("Namespace: %s", namespace)
            ns_name = namespace.metadata.name
            ns_list.append(ns_name)
        return ns_list

    def exec_command(self, ns_name: str, pod_name: str, exec_command):
        print(f"Run command : {' '.join(exec_command)}")
        resp = None
        try:
            resp = self.v1.read_namespaced_pod(name=pod_name, namespace=ns_name)
        except ApiException as e:
            if e.status != 404:
                print(f"Unknown error: {e}")
                exit(1)

        if not resp:
            print(f"Pod {pod_name} does not exist")
            return 1

        # Calling exec and waiting for response
        # exec_command = [
        #     '/bin/sh',
        #     '-c',
        #     'echo This message goes to stderr; echo This message goes to stdout']
        # When calling a pod with multiple containers running the target container
        # has to be specified with a keyword argument container=<name>.
        resp = stream(self.v1.connect_get_namespaced_pod_exec,
                      pod_name,
                      ns_name,
                      command=exec_command,
                      stderr=True, stdin=False,
                      stdout=True, tty=False)
        print("Response: " + resp)

        # Calling exec interactively
        # exec_command = ['/bin/sh']
        # resp = stream(self.v1.connect_get_namespaced_pod_exec,
        #               pod_name,
        #               ns_name,
        #               command=exec_command,
        #               stderr=True, stdin=True,
        #               stdout=True, tty=False,
        #               _preload_content=False)
        # commands = [
        #     "echo This message goes to stdout",
        #     "echo \"This message goes to stderr\" >&2",
        # ]
        #
        # while resp.is_open():
        #     resp.update(timeout=1)
        #     if resp.peek_stdout():
        #         print(f"STDOUT: {resp.read_stdout()}")
        #     if resp.peek_stderr():
        #         print(f"STDERR: {resp.read_stderr()}")
        #     if commands:
        #         c = commands.pop(0)
        #         print(f"Running command... {c}\n")
        #         resp.write_stdin(c + "\n")
        #     else:
        #         break
        #
        # resp.write_stdin("date\n")
        # sdate = resp.readline_stdout(timeout=3)
        # print(f"Server date command returns: {sdate}")
        # resp.write_stdin("whoami\n")
        # user = resp.readline_stdout(timeout=3)
        # print(f"Server user is: {user}")
        # resp.close()
        return 0

    def get_pod(self, ipod, ns_name: str | None, pod_name: str | None):
        i_ns_name = ipod.metadata.namespace
        if ns_name is not None:
            if i_ns_name != ns_name:
                self.logger.debug("Skip namespace %s", i_ns_name)
                return None, None, None
        i_pod_name = ipod.metadata.name
        if pod_name is not None:
            if i_pod_name != pod_name:
                self.logger.debug("Skip pod %s", i_pod_name)
                return None, None, None
        i_pod_ip = ipod.status.pod_ip
        if i_pod_ip is None:
            i_pod_ip = "---"
        self.logger.debug("Found pod %s:\n%s", i_pod_name, ipod)
        return i_pod_name, i_pod_ip, i_ns_name

    def get_pods(self, ns_name: str | None, pod_name: str | None):
        # Configs can be set in Configuration class directly or using helper utility
        # config.load_kube_config()
        #
        # v1 = client.CoreV1Api()
        self.logger.info("Listing pods with their IPs for namespace %s", ns_name)
        ipods = {}
        if pod_name:
            self.logger.info("Reod pod %s", pod_name)
        else:
            self.logger.info("Read pods")
        if ns_name:
            self.logger.info("Use namespace %s", ns_name)
        ret = self.v1.list_pod_for_all_namespaces(watch=False)
        for ipod in ret.items:
            pod_nm, pod_ip, pod_ns = self.get_pod(ipod, ns_name, pod_name)
            if pod_nm is not None:
                ipods[pod_nm] = (pod_ip, pod_ns)
        self.logger.info("Found %d pods", len(ipods))
        return ipods

    def get_service(self, isvc, ns_name: str | None, svc_name: str | None):
        isvc_ns = isvc.metadata.namespace
        if ns_name is not None:
            if isvc_ns != ns_name:
                self.logger.debug("Skip namespace %s", isvc_ns)
                return None, None, None, None, None
        isvc_name = isvc.metadata.name
        if svc_name is not None:
            if svc_name != isvc_name:
                self.logger.debug("Skip service %s", isvc_name)
                return None, None, None, None, None
        self.logger.debug("Service %s:\n%s", isvc_name, isvc)
        try:
            svc_ip = isvc.status.load_balancer.ingress[0].ip
            svc_port = str(isvc.spec.ports[0].port)
            svc_prot = isvc.spec.ports[0].protocol
        except TypeError:
            svc_ip = "---"
            svc_port = ""
            svc_prot = ""
        return isvc_name, isvc_ns, svc_ip, svc_port, svc_prot

    def get_services(self, ns_name: str | None, svc_name: str | None):
        """
            $ kubectl --namespace integration get service tango-databaseds -o json | jq -r .status.loadBalancer.ingress[].ip
        10.164.10.5
            $ kubectl --namespace integration get service tango-databaseds -o json | jq -r '.spec.ports[0]["port"]?'
        10000
            :param v1: k8s handle
            :param ns_name: namespace
            :param svc_name: service name
            :return:
        """
        svcs = {}
        if svc_name:
            self.logger.info("Read service %s", svc_name)
        else:
            self.logger.info("Read services")
        if ns_name:
            self.logger.info("Use namespace %s", ns_name)
        services = self.v1.list_service_for_all_namespaces(watch=False)
        for isvc in services.items:
            svc_nm, svc_ns, svc_ip, svc_port, svc_prot = self.get_service(
                isvc, ns_name, svc_name
            )
            if svc_nm is not None:
                svcs[svc_nm] = (svc_ns, svc_ip, svc_port, svc_prot)
        self.logger.info("Found %d services", len(svcs))
        return svcs

    def get_service_addr(self, isvc, ns_name: str | None, svc_name: str | None):
        """

        :param isvc: K8S service handle
        :param ns_name: namespace
        :param svc_name: service name
        :return: tuple with service name, namespace, IP address, port, protocol
        """
        isvc_ns = isvc.metadata.namespace
        if ns_name is not None:
            if isvc_ns != ns_name:
                self.logger.debug("Skip namespace %s", isvc_ns)
                return
        isvc_name = isvc.metadata.name
        if svc_name is not None:
            if svc_name != isvc_name:
                self.logger.debug("Skip service %s", isvc_name)
                return
        self.logger.debug("Service %s:\n%s", isvc_name, isvc)
        try:
            svc_ip = isvc.status.load_balancer.ingress[0].ip
            svc_port = str(isvc.spec.ports[0].port)
            svc_prot = isvc.spec.ports[0].protocol
        except TypeError:
            svc_ip = "---"
            svc_port = ""
            svc_prot = ""
        return isvc_name, isvc_ns, svc_ip, svc_port, svc_prot

    # def get_tangodb(self, ns_name: str, svc_name: str):
    #     """
    #     Read IP address and port for a service (e.g. Tango database) from Kubernetes cluster
    #
    #     :param ns_name: namespace name
    #     :param svc_name: service name
    #     :return: none
    #     """
    #     if svc_name:
    #         print(f"Service {svc_name}", end="")
    #     else:
    #         print("Services", end="")
    #     if ns_name:
    #         print(f" in namespace {ns_name}", end="")
    #     print()
    #     services = self.v1.list_service_for_all_namespaces(watch=False)
    #     self.logger.info("Read %d services", len(services.items))
    #     svcs = []
    #     for isvc in services.items:
    #         try:
    #             svc_nm, svc_ns, svc_ip, svc_port, svc_prot = self.get_service_addr(
    #                 isvc, ns_name, svc_name
    #             )
    #             print(f"{svc_ip:<15}  {svc_port:<5}  {svc_prot:<8} {svc_ns:<64}  {svc_nm}")
    #         except TypeError:
    #             pass
