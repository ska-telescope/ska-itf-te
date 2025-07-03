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
    settings["helm_releases"] = ["central-controller", "ska001-dish"]

    return settings


def test_helm_install(settings):
    """ Checks that the HelmReleases successfully installed all charts.
    """
    # Load kubeconfig and initialize client
    config.load_kube_config()
    crd_api = client.CustomObjectsApi()

    helmrelease_namespace = "flux-services"
    group = "helm.toolkit.fluxcd.io"
    version = "v2"
    plural = "helmreleases"

    # Get list of helmreleases in the namespace
    helm_releases = crd_api.list_namespaced_custom_object(group, version, helmrelease_namespace, plural)
    helm_releases_list = helm_releases.get("items", [])

    # Check that there are helmreleases in the namespace
    assert helm_releases_list, f"No HelmReleases found in namespace: {helmrelease_namespace}"

    # Get helmrelease of interest
    helmrelease_names = settings["helm_releases"]
    for helm_release_name in helmrelease_names:
        helm_release = next((helm_release for helm_release in helm_releases_list if helm_release["metadata"]["name"] == helm_release_name), None)

        if helm_release is not None:
            status = helm_release.get("status", {})
            conditions = status.get("conditions", [])
            ready_condition = next((cond for cond in conditions if cond.get("type") == "Ready"), None)
            ready_status = ready_condition.get("status") if ready_condition else "Unknown"
            ready_condition_message = ready_condition.get("message") if ready_condition else "No message available"
            logger.debug(f"HelmRelease {helm_release_name} Message: {ready_condition_message}")
            logger.info(f"HelmRelease {helm_release_name} Ready: {ready_status}")
        else:
            logger.info(f"HelmRelease {helm_release_name} not found in namespace: {helmrelease_namespace}")
        
        # Check that all helmreleases are ready
        assert ready_status == "True", f"HelmRelease {helm_release_name} is not ready. Status: {ready_status}. Message: {ready_condition_message}"


def test_device_servers(settings):
    """ Checks that the deployed Tango device servers are present and running.
    """
    
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

    # Check that device servers are present in the namespace
    assert device_servers_list, f"No DeviceServers found in the namespace: {namespace}."

    # Get number of device servers found in namespace
    num_device_servers = len(device_servers_list)
    logger.info(f"Found {num_device_servers} DeviceServers in namespace: {namespace}.")
    
    # Check that each DeviceServer is in the Running state
    for device_server in device_servers_list:
        name = device_server["metadata"]["name"]
        status = device_server.get("status", {})
        state = status.get("state")
        logger.debug(f"{name}, {state}")
        
        assert state == "Running", f"DeviceServer {name} not running. Actual state: {state}"
        

def test_telescope_state():
    pass
