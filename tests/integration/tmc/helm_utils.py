"""Helm helper utilities used by the upgrade/redeploy step definitions in conftest.py."""

import json
import logging
import subprocess
from time import sleep, time

import pytest
from ska_control_model import ObsState

logger = logging.getLogger(__name__)

# Grace period after all devices report reachable, allowing LRC executors and Tango
# event subscriptions across the CSP/SDP/Dish command chain to fully settle before the
# next AssignResources/Configure is attempted (see AT-3753 upgrade path timeouts).
POST_UPGRADE_SETTLE_TIME = 30

SKA_HELM_REPO_NAME = "ska"
SKA_HELM_REPO_URL = "https://artefact.skao.int/repository/helm-internal"
SKA_MID_CHART_NAME = "ska-mid"


def _ensure_helm_repo(
    repo_name: str = SKA_HELM_REPO_NAME, repo_url: str = SKA_HELM_REPO_URL
) -> None:
    """Add (or update) a helm repository.

    Equivalent helm commands:
       helm repo add <repo_name> <repo_url> --force-update
       helm repo update <repo_name>

    :param repo_name: Helm repository alias, defaults to SKA_HELM_REPO_NAME.
    :type repo_name: str
    :param repo_url: Helm repository URL, defaults to SKA_HELM_REPO_URL.
    :type repo_url: str
    """
    # Equivalent helm commands:
    #   helm repo add <repo_name> <repo_url> --force-update
    subprocess.run(
        ["helm", "repo", "add", repo_name, repo_url, "--force-update"],
        check=True,
        capture_output=True,
    )
    # Equivalent helm command:
    #   helm repo update <repo_name>
    subprocess.run(
        ["helm", "repo", "update", repo_name],
        check=True,
        capture_output=True,
    )


def _get_helm_release(namespace: str, chart_name: str = SKA_MID_CHART_NAME) -> dict | None:
    """Return the helm release dict for chart_name in namespace, or None if not found.

    Equivalent helm command:
       helm list -n <namespace> --output json

    :param namespace: Kubernetes namespace to search.
    :type namespace: str
    :param chart_name: Chart name prefix to match, defaults to SKA_MID_CHART_NAME.
    :type chart_name: str
    :return: Helm release dict, or None if no matching release exists.
    :rtype: dict | None
    """
    result = subprocess.run(
        ["helm", "list", "-n", namespace, "--output", "json"],
        stdout=subprocess.PIPE,
        check=True,
    )
    helm_list = json.loads(result.stdout)
    return next(
        (c for c in helm_list if c.get("chart", "").startswith(f"{chart_name}-")),
        None,
    )

def _upgrade_helm_release(
    release_name: str,
    namespace: str,
    version: str,
    chart_ref: str = f"{SKA_HELM_REPO_NAME}/{SKA_MID_CHART_NAME}",
) -> None:
    """In-place helm upgrade, reusing existing values.

    Equivalent helm command:
       helm upgrade <release_name> <chart_ref> --version <version> --namespace <namespace> \
           --reuse-values --wait --timeout 20m

    :param release_name: Helm release name to upgrade.
    :type release_name: str
    :param namespace: Kubernetes namespace the release lives in.
    :type namespace: str
    :param version: Target chart version.
    :type version: str
    :param chart_ref: Helm chart reference (repo/chart), defaults to ska/ska-mid.
    :type chart_ref: str
    """
    logger.info(f"Upgrading '{release_name}' in namespace '{namespace}' to version '{version}'")
    subprocess.run(
        [
            "helm",
            "upgrade",
            release_name,
            chart_ref,
            "--version",
            version,
            "--namespace",
            namespace,
            "--reuse-values",
            "--wait",
            "--timeout",
            "20m",
        ],
        check=True,
    )


def _wait_for_dish_devices(dishes: list, version: str, poll_timeout: int = 300) -> None:
    """Poll dish-manager device proxies until all dishes are reachable.

    A dish-lmc release being helm-ready does not guarantee its Tango device server is
    already accepting connections, so this is polled separately (and before the SUT
    upgrade begins) since the SUT cannot talk to the dishes until they are up.

    :param dishes: List of Dish helper objects to poll.
    :type dishes: list
    :param version: Chart version string used in the failure message.
    :type version: str
    :param poll_timeout: Maximum seconds to wait for devices, defaults to 300.
    :type poll_timeout: int
    """
    poll_interval = 10
    deadline = time() + poll_timeout
    logger.info("Waiting for dish-lmc Tango devices to be reachable...")
    while time() < deadline:
        try:
            for dish in dishes:
                dish.get_dish_manager_proxy()
            logger.info("All dish-lmc Tango devices are reachable")
            return
        except Exception as exc:
            logger.debug(
                f"Dish-lmc devices not yet reachable: {exc}. Retrying in {poll_interval}s..."
            )
            sleep(poll_interval)
    pytest.fail(
        f"Dish-lmc Tango devices did not become reachable within {poll_timeout}s "
        f"after upgrading to version '{version}'"
    )


def _wait_for_tango_devices(telescope_handlers, version: str, poll_timeout: int = 300) -> None:
    """Poll Tango device proxies until all are reachable, failing if timeout is exceeded.

    A bare ``ping()`` only confirms the device server process is answering the Tango DB -
    it does not confirm that a device's component manager has finished (re)establishing
    its own downstream connections/event subscriptions after the pod restart caused by the
    upgrade. The dish leaf nodes in particular are recreated by this same upgrade and depend
    on a live connection back to the (already-upgraded) dish-lmc DishManager devices, and the
    subarray node depends on CSP/SDP/dish leaf nodes reporting obsState correctly. Reading
    ``dishMode``/``obsState`` after ping succeeds exercises that whole chain, not just
    liveness of the process itself.

    :param telescope_handlers: Tuple of (TMC, CBF, CSP, dishes) telescope handler objects.
    :param version: Chart version string used in the failure message.
    :type version: str
    :param poll_timeout: Maximum seconds to wait for devices, defaults to 300.
    :type poll_timeout: int
    """
    tmc, _, csp, dishes = telescope_handlers
    tango_devices = [
        tmc.central_node,
        tmc.subarray_node,
        tmc.sdp_subarray_leaf_node,
        tmc.csp_master_leaf_node,
        tmc.csp_subarray_leaf_node,
        tmc.sdp_master_leaf_node,
        csp.control,
        csp.subarray,
    ]
    poll_interval = 10
    deadline = time() + poll_timeout
    logger.info("Waiting for Tango devices to be reachable...")
    while time() < deadline:
        try:
            for dp in tango_devices:
                dp.ping()
            for dish in dishes:
                _ = tmc.get_dish_leaf_node_dp(dish.dish_id).dishMode
            assert tmc.subarray_node.obsState == ObsState.EMPTY, (
                f"subarray_node.obsState is {tmc.subarray_node.obsState!s}, expected EMPTY"
            )
            logger.info("All Tango devices are reachable")
            break
        except Exception as exc:
            logger.debug(
                f"Tango devices not yet reachable: {exc}. Retrying in {poll_interval}s..."
            )
            sleep(poll_interval)
    else:
        pytest.fail(
            f"Tango devices did not become reachable within {poll_timeout}s after version "
            f"'{version}'"
        )

    logger.info(
        f"Waiting {POST_UPGRADE_SETTLE_TIME}s for command chains to settle after upgrade..."
    )
    sleep(POST_UPGRADE_SETTLE_TIME)


def _dish_namespace(sut_namespace: str, dish_id: str) -> str:
    """Return the dish-lmc namespace name for a given SUT namespace and dish ID.

    :param sut_namespace: SUT namespace (e.g. 'integration' or 'staging').
    :type sut_namespace: str
    :param dish_id: Dish ID with the SKA prefix, e.g. 'SKA001'.
    :type dish_id: str
    :return: Derived dish-lmc namespace name, e.g. 'integration-dish-lmc-ska001'.
    :rtype: str
    """
    return f"{sut_namespace}-dish-lmc-{dish_id.lower()}"
