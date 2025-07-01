import pytest
import subprocess
import logging
from kubernetes import client, config

logger = logging.getLogger(__name__)

@pytest.fixture(scope="module")
def settings():
    """ Deployment smoke test settings.
    TODO: Couple with integration test settings
    """

    settings = {}
    settings["SUT_namespace"] = "ska-mid-central-controller"

    return settings


def test_helm_install():
    pass


def test_device_servers(settings):
    """Checks that the deployed Tango device servers are present and running."""
    
    # Load kubeconfig and initialize client
    namespace = settings["SUT_namespace"]
    config.load_kube_config()
    crd_api = client.CustomObjectsApi()

    group = "tango.tango-controls.org"
    version = "v2"
    plural = "deviceservers"

    # Get info on all DeviceServers in the specified namespace using the CRD API
    device_servers = crd_api.list_namespaced_custom_object(group, version, namespace, plural)
    device_servers_list = device_servers.get("items", [])

    # Validate device servers list. Ensure not empty.
    num_device_servers = len(device_servers_list)
    logger.info(f"Found {num_device_servers} DeviceServers in namespace: {namespace}.")
    assert num_device_servers > 0, f"No DeviceServers found in the namespace: {namespace}."

    # Check that each DeviceServer is in the Running state
    for device_server in device_servers_list:
        name = device_server["metadata"]["name"]
        status = device_server.get("status", {})
        state = status.get("state")
        logger.debug(f"{name}, {state}")
        
        assert state in ("Running"), f"DeviceServer {name} not running. Actual state: {state}"


def test_telescope_state():
    pass
