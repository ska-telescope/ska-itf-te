from pytest_bdd import given, scenario, then
from kubernetes.client.models.v1_service import V1Service
import logging

@scenario(
    "features/ds_sim_connection.feature",
    "Connect to Dish Structure Simulators post-deployment",
)
def test_connection_to_ds_sim():
    """Connect to Dish Structure Simulators post-deployment."""

@given("the dish structure simulator is deployed in the Mid ITF")
def ds_sim_deployed(ds_sim_svc: V1Service):
    logging.debug("ds_sim_deployed")

@given("its connection details can be retrieved")
def connection_details(ds_sim_ip: str, ds_sim_http_port: int, ds_sim_discover_port: int, ds_sim_opcua_port: int):
    logging.debug(
        "ds-sim connection details: ip=%s, http_port=%s, discover_port=%s, opcua_port=%s",
        ds_sim_ip, ds_sim_http_port, ds_sim_discover_port, ds_sim_opcua_port,
    )

@when("the OPCUA client connects to it")
def opcua_client_connect_ds_sim(opcua_client):
    logging.debug("opcua_client connected")


# DS_SIM_HOST=$(kubectl -n ${DS_SIM_NAMESPACE} get svc ${DS_SIM_SERVICE} -o jsonpath={.status.loadBalancer.ingress[0].ip})
# DS_SIM_HTTP_PORT=$(kubectl get svc -n ${DS_SIM_NAMESPACE} ${DS_SIM_SERVICE} -o jsonpath='{.spec.ports[?(@.name=="server")].port}')
# DS_SIM_DISCOVER_PORT=$(kubectl get svc -n ${DS_SIM_NAMESPACE} ${DS_SIM_SERVICE} -o jsonpath='{.spec.ports[?(@.name=="discover")].port}')
# DS_SIM_OPCUA_PORT=$(kubectl get svc -n ${DS_SIM_NAMESPACE} ${DS_SIM_SERVICE} -o jsonpath='{.spec.ports[?(@.name=="opcua")].port}')