from kubernetes import client, config
from kubernetes.client.models.v1_service import V1Service
from kubernetes.client.models.v1_service_status import V1ServiceStatus
from kubernetes.client.models.v1_load_balancer_status import V1LoadBalancerStatus
from kubernetes.client.models.v1_load_balancer_ingress import V1LoadBalancerIngress
from kubernetes.client.models.v1_service_spec import V1ServiceSpec
from kubernetes.client.models.v1_service_port import V1ServicePort
from kubernetes.client.models.v1_condition import V1Condition

import pytest
import logging
from ska_ser_logging import configure_logging
from asyncua import Client

@pytest.fixture(scope="session", autouse=True)
def before_all(request):
    configure_logging(level=logging.DEBUG)

@pytest.fixture
def ds_sim_svc():
    config.load_kube_config()
    v1 = client.CoreV1Api()
    svc = v1.read_namespaced_service(name="ds-sim", namespace="ds-sim", pretty="true")
    yield svc

@pytest.fixture
def ds_sim_ip(ds_sim_svc: V1Service):
    status = V1ServiceStatus(ds_sim_svc.status).to_dict()
    logging.debug("status: %s", status)
    ip = status["conditions"]["load_balancer"]["ingress"][0]["ip"]
    logging.debug("ip: %s", ip)
    yield ip

@pytest.fixture
def ds_sim_http_port(ds_sim_svc: V1Service):
    port = get_svc_port(ds_sim_svc=ds_sim_svc, name="server")
    yield port

@pytest.fixture
def ds_sim_discover_port(ds_sim_svc: V1Service):
    port = get_svc_port(ds_sim_svc=ds_sim_svc, name="discover")
    yield port

@pytest.fixture
def ds_sim_opcua_port(ds_sim_svc: V1Service):
    port = get_svc_port(ds_sim_svc=ds_sim_svc, name="opcua")
    yield port

def get_svc_port(ds_sim_svc: V1Service, name: str) -> int:
    spec = V1ServiceSpec(ds_sim_svc.spec).to_dict()
    ports = spec["allocate_load_balancer_node_ports"]["ports"]
    logging.debug("ports: %s", ports)
    for p in ports:
        if p["name"] == name:
            return int(p["port"])
    raise MissingPortException(f"port {name} not found in ds-sim service")

class MissingPortException(Exception):
    pass

@pytest.fixture
def opcua_url(ds_sim_ip: str, ds_sim_discover_port: int):
    url = f"opc.tcp://{ds_sim_ip}:{ds_sim_discover_port}/OPCUA/SimpleServer"
    yield url

@pytest.fixture
def opcua_client(opcua_url: str):
    client = Client(url=opcua_url)
    yield client
    client.close_session()
