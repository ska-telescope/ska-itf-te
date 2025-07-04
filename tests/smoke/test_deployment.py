"""Deployment smoke tests."""

import pytest
import logging
from kubernetes import client, config

from ska_control_model._dev_state import DevState
from utils.telescope_teardown import TelescopeState, TelescopeHandler

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def deployment_smoke_test_settings(settings):
    """Deployment smoke test settings.

    TODO: Couple with integration test settings

    :return: _description_
    :rtype: _type_
    """
    deployment_smoke_test_settings = {}
    deployment_smoke_test_settings["SUT_namespace"] = settings["SUT_namespace"]
    deployment_smoke_test_settings["receptors"] = settings["dish_ids"]
    deployment_smoke_test_settings["cluster_domain"] = settings["sut_cluster_domain"]
    deployment_smoke_test_settings["helm_releases"] = ["central-controller", "ska001-dish"]
    logger.info(deployment_smoke_test_settings)

    return deployment_smoke_test_settings


def test_helm_install(deployment_smoke_test_settings):
    """Checks that the HelmReleasesi successfully installed all charts.

    :param deployment_smoke_test_settings: Deployment smoke test settings
    :type deployment_smoke_test_settings: dict
    """
    # Load kubeconfig and initialize client
    config.load_kube_config()
    crd_api = client.CustomObjectsApi()

    helmrelease_namespace = "flux-services"
    group = "helm.toolkit.fluxcd.io"
    version = "v2"
    plural = "helmreleases"

    # Get list of helmreleases in the namespace
    helm_releases = crd_api.list_namespaced_custom_object(
        group, version, helmrelease_namespace, plural
    )
    helm_releases_list = helm_releases.get("items", [])

    # Check that there are helmreleases in the namespace
    assert helm_releases_list, f"No HelmReleases found in namespace: {helmrelease_namespace}"

    helmrelease_names = deployment_smoke_test_settings["helm_releases"]

    # Find details of helmreleases of interest
    for helm_release_name in helmrelease_names:
        # Get helmrelease of interest
        helm_release = next(
            (
                helm_release
                for helm_release in helm_releases_list
                if helm_release["metadata"]["name"] == helm_release_name
            ),
            None,
        )

        if helm_release is not None:
            status = helm_release.get("status", {})
            conditions = status.get("conditions", [])

            # Find the Ready condition
            ready_condition = next(
                (condition for condition in conditions if condition.get("type") == "Ready"), None
            )

            # Get ready status, message, chart and chart version
            ready_status = ready_condition.get("status") if ready_condition else None
            ready_condition_message = (
                ready_condition.get("message") if ready_condition else None
            )
            chart = helm_release.get("spec", {}).get("chart", {}).get("spec", {}).get("chart")
            version = helm_release.get("spec", {}).get("chart", {}).get("spec", {}).get("version")

            logger.debug(f"HelmRelease {helm_release_name} Message: {ready_condition_message}")
            logger.info(f"HelmRelease {helm_release_name} Ready: {ready_status}")
            logger.info(f"HelmRelease {helm_release_name} chart: {chart}, version: {version}")
        else:
            logger.info(
                f"HelmRelease {helm_release_name} not found in namespace: {helmrelease_namespace}"
            )

        # Check that all helmreleases are ready
        assert ready_status == "True", (
            f"HelmRelease {helm_release_name} is not ready. "
            f"Status: {ready_status}. Message: {ready_condition_message}"
        )


def test_device_servers(deployment_smoke_test_settings):
    """Checks that the deployed Tango device servers are present and running.

    :param deployment_smoke_test_settings: Deployment smoke test settings
    :type deployment_smoke_test_settings: dict
    """
    # Load kubeconfig and initialize client
    namespace = deployment_smoke_test_settings["SUT_namespace"]
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
        

def test_telescope_state(deployment_smoke_test_settings):
    """Checks that the telescope is in a usable state.

    :param deployment_smoke_test_settings: Deployment smoke test settings
    :type deployment_smoke_test_settings: dict
    """
    namespace = deployment_smoke_test_settings["SUT_namespace"]
    cluster_domain = deployment_smoke_test_settings["cluster_domain"]
    receptors = deployment_smoke_test_settings["receptors"]

    # Base state (telescope=OFF, Subarray,CSP,SDP=EMPTY, dishes=STANBY_LP)
    telescope_state_off = TelescopeState()

    # Also a valid base state, pending TMC state aggregation improvement
    telescope_state_off_central_node_unknown = TelescopeState(central_node=DevState.UNKNOWN)

    # List of expected "healthy" telescope states
    allowed_states = [telescope_state_off_central_node_unknown, telescope_state_off]

    # Get the current telescope state
    telescope_handler = TelescopeHandler(namespace, cluster_domain, receptors)
    current_state = telescope_handler.get_current_state()

    assert current_state in allowed_states, (
        "Expected telescope state to be one of: "
        f"{allowed_states},\n\nActual telescope state: {current_state}"
    )
    