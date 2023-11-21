"""Fixtures and setup for dish structure simulator testing."""
import asyncio
import logging
import os
from pathlib import Path
from typing import Generator

import pytest
from asyncua import Client
from asyncua.crypto.cert_gen import setup_self_signed_certificate
from asyncua.crypto.security_policies import SecurityPolicyBasic256
from asyncua.ua import MessageSecurityMode
from cryptography.x509.oid import ExtendedKeyUsageOID
from kubernetes import client, config
from kubernetes.client.models.v1_service import V1Service
from kubernetes.client.models.v1_service_spec import V1ServiceSpec
from kubernetes.client.models.v1_service_status import V1ServiceStatus
from ska_ser_logging import configure_logging


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


@pytest.fixture(name="opcua_user")
def fixture_opcua_user() -> Generator:
    """
    OPCUA user to authenticate with.

    :yield: OPCUA user as a string
    :rtype: Generator
    """
    user = os.environ["DS_SIM_USER"]
    yield user


@pytest.fixture(name="opcua_password")
def fixture_opcua_password() -> Generator:
    """
    OPCUA password to authenticate with.

    :yield: OPCUA password as a string
    :rtype: Generator
    """
    password = os.environ["DS_SIM_PASSWORD"]
    yield password


@pytest.fixture(name="opcua_server_cert")
def fixture_opcua_server_cert() -> Generator:
    """
    OPCUA server certificate path.

    :yield: OPCUA server certificate path as a Path
    :rtype: Generator
    """
    server_cert = Path(os.environ["DS_SIM_SERVER_CERT"])
    yield server_cert


@pytest.fixture(name="opcua_client_cert")
def fixture_opcua_client_cert() -> Generator:
    """
    Path to generate the OPCUA client certificate at.

    :yield: OPCUA client certificate path as a Path
    :rtype: Generator
    """
    client_cert = Path(Path(__file__).parent, "ds_sim_client_cert.der")
    yield client_cert


@pytest.fixture(name="opcua_client_key")
def fixture_opcua_client_key() -> Generator:
    """
    Path to generate OPCUA client key at.

    :yield: OPCUA client key path as a Path
    :rtype: Generator
    """
    client_key = Path(Path(__file__).parent, "ds_sim_client_key.pem")
    yield client_key


@pytest.fixture(name="opcua_client")
def fixture_opcua_client(
    opcua_url: str,
    opcua_user: str,
    opcua_password: str,
    opcua_server_cert: Path,
    opcua_client_cert: Path,
    opcua_client_key: Path,
) -> Generator:
    """
    OPCUA client fixture.

    :param opcua_url: The OPCUA URL to connect to.
    :type opcua_url: str
    :param opcua_user: The OPCUA user to authenticate with.
    :type opcua_user: str
    :param opcua_password: The OPCUA password to authenticate with.
    :type opcua_password: str
    :param opcua_server_cert: The OPCUA server certificate to for the security policy.
    :type opcua_server_cert: Path
    :param opcua_client_cert: The OPCUA client certificate to for the security policy.
    :type opcua_client_cert: Path
    :param opcua_client_key: The OPCUA client key to for the security policy.
    :type opcua_client_key: Path
    :yield: The OPCUA client.
    :rtype: Generator
    """
    loop = asyncio.get_event_loop()
    opcua_client = Client(url=opcua_url)
    opcua_client.set_user(opcua_user)
    opcua_client.set_password(opcua_password)
    client_app_uri = "urn:freeopcua:client"
    loop.run_until_complete(
        setup_self_signed_certificate(
            opcua_client_key,
            opcua_client_cert,
            client_app_uri,
            "localhost",
            [ExtendedKeyUsageOID.CLIENT_AUTH],
            {
                "countryName": "ZA",
                "stateOrProvinceName": "Western Cape",
                "localityName": "Cape Town",
                "organizationName": "SKAO",
            },
        )
    )
    loop.run_until_complete(
        opcua_client.set_security(
            SecurityPolicyBasic256,
            certificate=str(opcua_client_cert),
            private_key=str(opcua_client_key),
            server_certificate=str(opcua_server_cert),
            mode=MessageSecurityMode.Sign,
        )
    )
    # pytest-asyncio doesn't seem to work with pytest-bdd so we run until the Futures are done
    loop.run_until_complete(opcua_client.connect())
    yield opcua_client
    loop.run_until_complete(opcua_client.close_session())
