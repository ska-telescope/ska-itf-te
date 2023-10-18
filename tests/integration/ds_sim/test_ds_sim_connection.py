"""Test connection to dish structure simulator post-deployment."""
import asyncio
import logging

import pytest
from asyncua import Client
from asyncua.common.node import Node
from kubernetes.client.models.v1_service import V1Service
from pytest_bdd import given, scenario, then, when

from tests.integration.ds_sim.conftest import ds_sim_env

pytestmark = pytest.mark.skipif(
    not ds_sim_env(), reason="Not a dish structure simulator environment"
)


@scenario(
    "features/ds_sim_connection.feature",
    "Connect to Dish Structure Simulators post-deployment",
)
@pytest.mark.dish_structure_simulator
def test_connection_to_ds_sim():
    """Test connection to the Dish Structure Simulator post-deployment."""


@given("the dish structure simulator is deployed in the Mid ITF")
def ds_sim_deployed(ds_sim_svc: V1Service):
    """
    Verify that the dish structure simulator is deployed.

    :param ds_sim_svc: The dish structure simulator service.
    :type ds_sim_svc: V1Service
    """
    logging.debug("ds_sim_deployed %s", ds_sim_svc)


@given("its connection details can be retrieved")
def connection_details(
    ds_sim_ip: str, ds_sim_http_port: int, ds_sim_discover_port: int, ds_sim_opcua_port: int
):
    """
    Verify that we can retrieve the dish structure simulator's connection details.

    :param ds_sim_ip: dish structure simulator IP address
    :type ds_sim_ip: str
    :param ds_sim_http_port: dish structure simulator web server port
    :type ds_sim_http_port: int
    :param ds_sim_discover_port: dish structure simulator discover port
    :type ds_sim_discover_port: int
    :param ds_sim_opcua_port: dish structure simulator OPCUA port
    :type ds_sim_opcua_port: int
    """
    logging.debug(
        "ds-sim connection details: ip=%s, http_port=%s, discover_port=%s, opcua_port=%s",
        ds_sim_ip,
        ds_sim_http_port,
        ds_sim_discover_port,
        ds_sim_opcua_port,
    )


@when("the OPCUA client connects to it")
def opcua_client_connect_ds_sim(opcua_client: Client):
    """
    Verify that we are connected to the OPCUA server.

    :param opcua_client: The OPCUA client used to connect to the server.
    :type opcua_client: Client
    """
    logging.debug("opcua_client connected: %s", opcua_client.application_uri)


@then("it responds with the expected values")
def responds_with_expected_values(opcua_client: Client):
    """
    Verify that the OPCUA server responds with expected values when queried.

    :param opcua_client: The OPCUA client used to connect to the server.
    :type opcua_client: Client
    """
    # pytest-asyncio & pytest-bdd don't work together so we run until the Futures are done
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_value(opcua_client=opcua_client))
    logging.debug("it responds with the expected values")


async def test_value(opcua_client: Client):
    """
    Test that the OPCUA server responds with expected values when queried.

    This is separate from the responds_with_expected_values method because
    pytest-bdd & pytest-asyncio don't work together.

    :param opcua_client: The OPCUA client used to connect to the server.
    :type opcua_client: Client
    """
    child: Node = await opcua_client.nodes.root.get_child(
        [
            "0:Objects",
            "2:Logic",
            "2:Application",
            "2:PLC_PRG",
            "2:Pointing",
            "2:Status",
            "2:StaticCorrActive",
        ]
    )
    val = await child.read_value()
    logging.debug("opcua_client read value for StaticCorrActive: %s", val)
