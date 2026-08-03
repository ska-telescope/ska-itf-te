"""Helm helper utilities used by the upgrade/redeploy step definitions in conftest.py."""

import json
import logging
import os
import subprocess
import tempfile
from time import sleep, time

import pytest
from tango import DeviceProxy

logger = logging.getLogger(__name__)

SKA_HELM_REPO_NAME = "ska"
SKA_HELM_REPO_URL = "https://artefact.skao.int/repository/helm-internal"
SKA_MID_CHART_NAME = "ska-mid"

# Core TMC/CSP device names used to verify Tango readiness after a redeploy.
# DeviceProxy objects are created fresh on every poll attempt so that no
# pre-existing (potentially stale) proxies are required.
_TANGO_CORE_DEVICE_NAMES = [
    "mid-tmc/central-node/0",
    "mid-tmc/subarray/01",
    "mid-tmc/subarray-leaf-node-sdp/01",
    "mid-tmc/leaf-node-csp/0",
    "mid-tmc/subarray-leaf-node-csp/01",
    "mid-tmc/leaf-node-sdp/0",
    "mid-csp/control/0",
    "mid-csp/subarray/01",
]


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
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Equivalent helm command:
    #   helm repo update <repo_name>
    subprocess.run(
        ["helm", "repo", "update", repo_name],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
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


def _redeploy_helm_release(
    release_name: str,
    namespace: str,
    version: str,
    chart_ref: str = f"{SKA_HELM_REPO_NAME}/{SKA_MID_CHART_NAME}",
    delete_namespace: bool = True,
) -> None:
    """Uninstall a release, optionally delete its namespace, then reinstall at *version*.

    Current user-supplied values are captured before uninstall and reused on install
    so that dish-specific configuration (EDA params, SPFRX addresses, etc.) is preserved.

    Equivalent helm commands:
       helm uninstall <release_name> -n <namespace>
       [kubectl delete namespace <namespace>]
       helm install <release_name> <chart_ref> --version <version> --namespace <namespace> \
           --values <values_file>

    :param release_name: Helm release name to uninstall and reinstall.
    :type release_name: str
    :param namespace: Kubernetes namespace the release lives in.
    :type namespace: str
    :param version: Chart version to install.
    :type version: str
    :param chart_ref: Helm chart reference (repo/chart), defaults to ska/ska-mid.
    :type chart_ref: str
    :param delete_namespace: Whether to delete the namespace before reinstalling,
        defaults to True.
    :type delete_namespace: bool
    """
    # Capture current user-supplied values
    values_result = subprocess.run(
        ["helm", "get", "values", release_name, "-n", namespace, "--output", "yaml"],
        stdout=subprocess.PIPE,
        check=True,
    )
    current_values_yaml = values_result.stdout

    # Uninstall
    logger.info(f"Uninstalling '{release_name}' from namespace '{namespace}'")
    subprocess.run(
        ["helm", "uninstall", release_name, "-n", namespace],
        check=True,
    )

    if delete_namespace:
        logger.info(f"Deleting namespace '{namespace}'")
        subprocess.run(["kubectl", "delete", "namespace", namespace], check=True)
        # Best-effort wait for the namespace to be fully removed
        subprocess.run(
            ["kubectl", "wait", "--for=delete", f"namespace/{namespace}", "--timeout=120s"],
            check=False,
        )

    # Reinstall with preserved values written to a temp file
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".yaml", delete=False) as values_file:
        values_file.write(current_values_yaml)
        values_path = values_file.name

    try:
        logger.info(
            f"Installing '{release_name}' from '{chart_ref}' version '{version}' "
            f"into namespace '{namespace}'"
        )
        subprocess.run(
            [
                "helm",
                "install",
                release_name,
                chart_ref,
                "--version",
                version,
                "--namespace",
                namespace,
                "--create-namespace",
                "--values",
                values_path,
                "--wait",
                "--timeout",
                "20m",
            ],
            check=True,
        )
    finally:
        os.unlink(values_path)


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


def _wait_for_tango_devices(telescope_handlers, version: str, poll_timeout: int = 300) -> None:
    """Poll Tango device proxies until all are reachable, failing if timeout is exceeded.

    :param telescope_handlers: Tuple of (TMC, CBF, CSP, dishes) telescope handler objects.
    :param version: Chart version string used in the failure message.
    :type version: str
    :param poll_timeout: Maximum seconds to wait for devices, defaults to 300.
    :type poll_timeout: int
    """
    tmc, _, csp, _ = telescope_handlers
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
            logger.info("All Tango devices are reachable")
            return
        except Exception as exc:
            logger.debug(
                f"Tango devices not yet reachable: {exc}. Retrying in {poll_interval}s..."
            )
            sleep(poll_interval)
    pytest.fail(
        f"Tango devices did not become reachable within {poll_timeout}s "
        f"after version '{version}'"
    )


def _wait_for_tango_by_name(version: str, poll_timeout: int = 300) -> None:
    """Poll core Tango devices by name until all are reachable.

    Creates fresh DeviceProxy objects on every attempt so that no pre-existing
    (potentially stale) proxy handles are required. Use this variant when
    Tango may not yet be reachable (e.g. immediately after a helm redeploy).

    :param version: Chart version string used in the failure message.
    :type version: str
    :param poll_timeout: Maximum seconds to wait for devices, defaults to 300.
    :type poll_timeout: int
    """
    poll_interval = 10
    deadline = time() + poll_timeout
    logger.info("Waiting for Tango devices to be reachable (by name)...")
    while time() < deadline:
        try:
            for name in _TANGO_CORE_DEVICE_NAMES:
                DeviceProxy(name).ping()
            logger.info("All Tango devices are reachable")
            return
        except Exception as exc:
            logger.debug(
                f"Tango devices not yet reachable: {exc}. Retrying in {poll_interval}s..."
            )
            sleep(poll_interval)
    pytest.fail(
        f"Tango devices did not become reachable within {poll_timeout}s "
        f"after version '{version}'"
    )


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


def _redeploy_sut_via_make(release_name: str, namespace: str, version: str) -> None:
    """Destroy and redeploy the SUT namespace using the same make targets as the CI.

    Mirrors the ``redeploy-sut-integration`` CI job: runs the ``.cleanup`` script
    (``pvc-patch-delete`` + ``k8s-uninstall-chart``) followed by the ``.deploy``
    script (``k8s-install-chart`` + ``pvc-patch-apply`` +
    ``taranta-deploy-all-tangogql-instances``), with ``K8S_SKIP_DEP_BUILD=true``
    and ``K8S_UMBRELLA_CHART_PATH`` overridden to install a specific version from
    the SKA CAR helm repository.

    This avoids the ``existingClaim`` PVC failure that occurs when saved helm values
    are reused after an ``helm uninstall``: by not passing ``--values`` from the old
    deployment the chart creates all PVCs fresh on reinstall, exactly as the CI does.

    :param release_name: Helm release name (e.g. 'integration-main').
    :type release_name: str
    :param namespace: SUT Kubernetes namespace (e.g. 'integration').
    :type namespace: str
    :param version: Chart version to install from CAR (e.g. '31.4.0').
    :type version: str
    """
    sdp_namespace = f"{namespace}-sdp"

    # ---- Destroy phase (mirrors .cleanup before_script) ----
    logger.info(f"Destroying SUT release '{release_name}' in namespace '{namespace}'...")
    subprocess.run(
        ["make", "pvc-patch-delete"],
        env={**os.environ, "KUBE_NAMESPACE_SDP": sdp_namespace},
        check=False,
    )
    subprocess.run(
        ["make", "remove-sut-deployment"],
        env={**os.environ, "HELM_RELEASE": release_name, "KUBE_NAMESPACE": namespace},
        check=False,
    )

    # ---- Deploy phase (mirrors .deploy script) ----
    # K8S_SKIP_DEP_BUILD=true skips 'helm dep build' (not valid for a CAR chart ref).
    # K8S_UMBRELLA_CHART_PATH is set to "ska/<chart> --version <X>" so that
    # k8s-do-install-chart expands it into:
    #   helm upgrade --install <release> $(K8S_CHART_PARAMS) ska/ska-mid --version X -n <ns>
    # No --values from the old deployment are passed, so the chart creates its PVCs fresh.
    logger.info(f"Deploying SUT from CAR version '{version}' into namespace '{namespace}'...")
    subprocess.run(
        [
            "make",
            "k8s-install-chart",
            "K8S_SKIP_DEP_BUILD=true",
            f"K8S_UMBRELLA_CHART_PATH=ska/{SKA_MID_CHART_NAME} --version {version}",
            f"HELM_RELEASE={release_name}",
            f"KUBE_NAMESPACE={namespace}",
        ],
        check=True,
    )

    # k8s-install-chart doesn't --wait, so confirm Jobs/CRs/Pods are ready before proceeding
    # (mirrors the "K8S wait" step run after k8s-install-chart in the CI pipeline).
    logger.info(f"Waiting for Jobs/Pods to be ready in namespace '{namespace}'...")
    subprocess.run(
        ["make", "k8s-wait"],
        env={**os.environ, "KUBE_NAMESPACE": namespace},
        check=True,
    )

    # Create the SDP data-product PVC (post-install, mirrors .deploy script)
    subprocess.run(
        ["make", "pvc-patch-apply"],
        env={**os.environ, "KUBE_NAMESPACE_SDP": sdp_namespace},
        check=True,
    )

    # Deploy TangoGQL for multi-DB Taranta access to dish namespaces
    if os.environ.get("DISH_LMC_IN_THE_LOOP", "false").lower() == "true":
        subprocess.run(
            ["make", "taranta-deploy-all-tangogql-instances"],
            env={**os.environ, "KUBE_NAMESPACE": namespace},
            check=False,
        )
