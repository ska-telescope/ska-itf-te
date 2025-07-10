"""Deployment smoke tests."""

import json
import logging
import subprocess

import pytest
from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException
from ska_control_model._dev_state import DevState
from tango import DeviceProxy

from utils.enums import DishMode
from utils.telescope_teardown import TelescopeHandler, TelescopeState

logger = logging.getLogger(__name__)
logging.getLogger("kubernetes.client.rest").setLevel(logging.WARNING)


@pytest.fixture(scope="module")
def deployment_smoke_test_settings(settings, receptor_ids):
    """Deployment smoke test settings.

    :param settings: Global settings
    :type settings: dict
    :param receptor_ids: List of receptors (dishes) in deployment
    :type receptor_ids: list
    :return: Deployment smoke test settings
    :rtype: dict
    """
    deployment_smoke_test_settings = {}
    deployment_smoke_test_settings["SUT_namespace"] = settings["SUT_namespace"]
    deployment_smoke_test_settings["receptors"] = receptor_ids
    deployment_smoke_test_settings["cluster_domain"] = settings["sut_cluster_domain"]
    deployment_smoke_test_settings["helm_releases"] = ["central-controller", "ska001-dish"]
    deployment_smoke_test_settings["chart_name"] = "ska-mid"
    logger.info(deployment_smoke_test_settings)

    return deployment_smoke_test_settings


def test_helm_install(deployment_smoke_test_settings, k8s_config):
    """Checks that the HelmReleasesi successfully installed all charts.

    :param deployment_smoke_test_settings: Deployment smoke test settings
    :type deployment_smoke_test_settings: dict
    :param k8s_config: Fixture providing Kubernetes configuration
    :type k8s_config: fixture
    """
    # Initialise Kubernetes client
    crd_api = client.CustomObjectsApi()

    if deployment_smoke_test_settings["cluster_domain"] == "mid.internal.skao.int":
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
                    (condition for condition in conditions if condition.get("type") == "Ready"),
                    None,
                )

                # Get ready status, message, chart and chart version
                ready_status = ready_condition.get("status") if ready_condition else None
                ready_condition_message = (
                    ready_condition.get("message") if ready_condition else None
                )
                chart = helm_release.get("spec", {}).get("chart", {}).get("spec", {}).get("chart")
                version = (
                    helm_release.get("spec", {}).get("chart", {}).get("spec", {}).get("version")
                )

                logger.debug(f"HelmRelease {helm_release_name} Message: {ready_condition_message}")
                logger.info(f"HelmRelease {helm_release_name} Ready: {ready_status}")
                logger.info(f"HelmRelease {helm_release_name} chart: {chart}, version: {version}")
            else:
                logger.info(
                    f"HelmRelease {helm_release_name} not found "
                    f"in namespace: {helmrelease_namespace}"
                )

            # Check that all helmreleases are ready
            assert ready_status == "True", (
                f"HelmRelease {helm_release_name} is not ready. "
                f"Status: {ready_status}. Message: {ready_condition_message}"
            )

    # Check that the chart of interest has been deployed in miditf
    # (Flux not being used in ITF env yet)
    deployed_chart_name = deployment_smoke_test_settings["chart_name"]
    if deployment_smoke_test_settings["cluster_domain"] == "miditf.internal.skao.int":
        namespace = deployment_smoke_test_settings["SUT_namespace"]
        result = subprocess.run(
            ["helm", "list", "-n", namespace, "--output", "json"], stdout=subprocess.PIPE
        )
        helm_list = json.loads(result.stdout)
        chart_deployed = False
        # Get name and status of deployed charts, look for ska-mid successful deployment
        for chart in helm_list:
            chart_name = chart.get("chart")
            status = chart.get("status")
            logger.info(f"Helm chart {chart_name} status: {status}")
            if f"{deployed_chart_name}-" in chart_name:
                assert (
                    status == "deployed"
                ), f"Helm chart {chart_name} is not deployed. Status: {status}"
                chart_deployed = True

        if not chart_deployed:
            assert False, f"{deployed_chart_name} chart has not been deployed"

    logger.info("Chart installation is complete")


def test_device_servers(deployment_smoke_test_settings, k8s_config):
    """Checks that the deployed Tango device servers are present and running.

    :param deployment_smoke_test_settings: Deployment smoke test settings
    :type deployment_smoke_test_settings: dict
    :param k8s_config: Fixture providing Kubernetes configuration
    :type k8s_config: fixture
    """
    # Initialise Kubernetes client
    crd_api = client.CustomObjectsApi()

    namespace = deployment_smoke_test_settings["SUT_namespace"]

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

        assert state == "Running", f"DeviceServer {name} not running. Actual state: {state}"
    logger.info("All device servers are running")


def test_telescope_state(deployment_smoke_test_settings):
    """Checks that the telescope is in a usable state.

    :param deployment_smoke_test_settings: Deployment smoke test settings
    :type deployment_smoke_test_settings: dict
    """
    namespace = deployment_smoke_test_settings["SUT_namespace"]
    cluster_domain = deployment_smoke_test_settings["cluster_domain"]
    receptors = deployment_smoke_test_settings["receptors"]

    # Base state (telescope=OFF, Subarray,CSP,SDP=EMPTY, dishes=STANBY_LP)
    base_dish_states = {receptor: DishMode.STANDBY_LP for receptor in receptors}
    telescope_state_off = TelescopeState(dishes=base_dish_states)

    # Also a valid base state, pending TMC state aggregation improvement
    telescope_state_off_central_node_unknown = TelescopeState(
        central_node=DevState.UNKNOWN, dishes=base_dish_states
    )

    # List of expected "healthy" telescope states
    allowed_states = [telescope_state_off_central_node_unknown, telescope_state_off]

    # Get the current telescope state
    telescope_handler = TelescopeHandler(namespace, cluster_domain, receptors)
    current_state = telescope_handler.get_current_state()

    assert current_state in allowed_states, (
        "Expected telescope state to be one of: "
        f"{allowed_states},\n\nActual telescope state: {current_state}"
    )

    logger.info("Telescope is in a useable state")


def test_devices_reachable(deployment_smoke_test_settings):
    """Tests connectivity to tango devices.

    This is a simple smoke test to check if the required devices are reachable.
    It creates device proxies to various tango devices and checks if they are reachable.

    :param deployment_smoke_test_settings: Deployment smoke test settings
    :type deployment_smoke_test_settings: dict
    """
    sut_namespace = deployment_smoke_test_settings["SUT_namespace"]
    cluster_domain = deployment_smoke_test_settings["cluster_domain"]
    central_node = DeviceProxy(
        f"tango-databaseds.{sut_namespace}.svc.{cluster_domain}" ":10000/mid-tmc/central-node/0"
    )
    subarray_node = DeviceProxy(
        f"tango-databaseds.{sut_namespace}.svc.{cluster_domain}" ":10000/mid-tmc/subarray/01"
    )

    devices = [central_node, subarray_node]

    for device in devices:
        try:
            device.ping()
        except Exception as e:
            logger.debug(e)
            pytest.fail(f"Device {device.name} is not reachable")

    logger.info(f"Checked devices reachable: {', '.join([device.name() for device in devices])}")


@pytest.fixture(scope="session")
def k8s_config():
    """Load Kubernetes configuration.

    Gets kuberenetes config using either kubeconfig or in-cluster service account config.
    :raises RuntimeError: If neither kubeconfig nor in-cluster config can be loaded
    """
    try:
        config.load_kube_config()
        logger.debug("Loaded local kubeconfig")
    except ConfigException:
        try:
            config.load_incluster_config()
            logger.debug("Loaded in-cluster config")
        except ConfigException:
            raise RuntimeError(
                "Failed to load Kubernetes config from both kubeconfig and in-cluster"
            )
