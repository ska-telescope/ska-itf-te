"""Fixtures and setup for dish structure simulator testing."""
import asyncio
import logging
import os
from typing import Generator

import pytest
from asyncua import Client
from kubernetes import client, config
from kubernetes.client.models.v1_service import V1Service
from kubernetes.client.models.v1_service_spec import V1ServiceSpec
from kubernetes.client.models.v1_service_status import V1ServiceStatus
from ska_ser_logging import configure_logging


def ds_sim_env() -> bool:
    """
    Determine whether this is a dish structure simulator test environment.

    :return: True if this is a dish structure simulator test environment, False otherwise.
    :rtype: bool
    """
    return os.getenv("DS_SIM_ENV") is not None


@pytest.fixture(scope="session", autouse=True)
def before_all():
    """Do setup for all tests."""
    configure_logging(level=logging.DEBUG)


@pytest.fixture(name="ds_sim_svc")
def fixture_ds_sim_svc() -> Generator:
    """
    Retrieve the dish structure simulator kubernetes service.

    :yield: The kubernetes service
    :rtype: Generator
    """
    ds_sim_svc_name = os.getenv("DS_SIM_SERVICE", "ds-sim")
    ds_sim_namespace = os.getenv("DS_SIM_NAMESPACE", "ds-sim")
    config.load_kube_config()
    client_v1 = client.CoreV1Api()
    svc = client_v1.read_namespaced_service(
        name=ds_sim_svc_name, namespace=ds_sim_namespace, pretty="true"
    )
    yield svc


@pytest.fixture(name="ds_sim_ip")
def fixture_ds_sim_ip(ds_sim_svc: V1Service) -> Generator:
    """
    Retrieve the service IP address.

    :param ds_sim_svc: The kubernetes service.
    :type ds_sim_svc: V1Service
    :yield: the IP address
    :rtype: Generator
    """
    status = V1ServiceStatus(ds_sim_svc.status).to_dict()
    logging.debug("status: %s", status)
    ip_address = status["conditions"]["load_balancer"]["ingress"][0]["ip"]
    logging.debug("ip_address: %s", ip_address)
    yield ip_address


@pytest.fixture(name="ds_sim_http_port")
def fixture_ds_sim_http_port(ds_sim_svc: V1Service) -> Generator:
    """
    Retrieve the web server port.

    :param ds_sim_svc: The kubernetes service.
    :type ds_sim_svc: V1Service
    :yield: The port number.
    :rtype: Generator
    """
    port = get_svc_port(ds_sim_svc=ds_sim_svc, name="server")
    yield port


@pytest.fixture(name="ds_sim_discover_port")
def fixture_ds_sim_discover_port(ds_sim_svc: V1Service) -> Generator:
    """
    Retrieve the discover port.

    :param ds_sim_svc: The kubernetes service.
    :type ds_sim_svc: V1Service
    :yield: The port number.
    :rtype: Generator
    """
    port = get_svc_port(ds_sim_svc=ds_sim_svc, name="discover")
    yield port


@pytest.fixture(name="ds_sim_opcua_port")
def fixture_ds_sim_opcua_port(ds_sim_svc: V1Service) -> Generator:
    """
    Retrieve the OPCUA port.

    :param ds_sim_svc: The kubernetes service.
    :type ds_sim_svc: V1Service
    :yield: The port number.
    :rtype: Generator
    """
    port = get_svc_port(ds_sim_svc=ds_sim_svc, name="opcua")
    yield port


def get_svc_port(ds_sim_svc: V1Service, name: str) -> int:
    """
    Retrieve a named port from the kubernetes service spec.

    :param ds_sim_svc: The kubernetes service.
    :type ds_sim_svc: V1Service
    :param name: The name of the port.
    :type name: str
    :raises MissingPortException: when the port is not present.
    :return: The port number.
    :rtype: int
    """
    spec = V1ServiceSpec(ds_sim_svc.spec).to_dict()
    ports = spec["allocate_load_balancer_node_ports"]["ports"]
    logging.debug("ports: %s", ports)
    for service_port in ports:
        if service_port["name"] == name:
            return int(service_port["port"])
    raise MissingPortException(f"port {name} not found in ds-sim service")


class MissingPortException(Exception):
    """
    Exception raised when an expected port is not present in the kubernetes spec.

    :param Exception: Exception base class
    :type Exception: Exception
    """


@pytest.fixture(name="opcua_url")
def fixture_opcua_url(ds_sim_ip: str, ds_sim_discover_port: int) -> Generator:
    """
    OPCUA URL fixture.

    :param ds_sim_ip: dish structure simulator IP address
    :type ds_sim_ip: str
    :param ds_sim_discover_port: dish structure simulator discover port
    :type ds_sim_discover_port: int
    :yield: OPCUA URL as a string
    :rtype: Generator
    """
    # Use Docker when testing locally: I haven't gotten OPCUA to work with minikube yet.
    # You will need to clone this repo:
    # https://gitlab.com/ska-telescope/ska-te-dish-structure-simulator
    # And run the container:
    #   cd images/ska-te-ds-web-sim
    #   ./buildme.sh
    #   ./runme.sh
    # Uncomment the following lines to have the test connect to the container:
    # ds_sim_ip = "127.0.0.1"
    # ds_sim_discover_port = 4840
    url = f"opc.tcp://{ds_sim_ip}:{ds_sim_discover_port}/OPCUA/SimpleServer"
    yield url


@pytest.fixture(name="opcua_client")
def fixture_opcua_client(opcua_url: str) -> Generator:
    """
    OPCUA client fixture.

    :param opcua_url: The OPCUA URL to connect to.
    :type opcua_url: str
    :yield: The OPCUA client.
    :rtype: Generator
    """
    loop = asyncio.get_event_loop()
    opcua_client = Client(url=opcua_url)
    # pytest-asyncio doesn't seem to work with pytest-bdd so we run until the Futures are done
    loop.run_until_complete(opcua_client.connect())
    yield opcua_client
    loop.run_until_complete(opcua_client.close_session())
