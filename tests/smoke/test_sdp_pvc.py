"""PVC is deployed with SUT feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


@scenario('features/sdp_pvc.feature', 'PVC deployment successful')
def test_pvc_deployment_successful():
    """PVC deployment successful."""


@given('a kubernetes cluster deployment of the SUT which includes the SDP')
def _():
    """a kubernetes cluster deployment of the SUT which includes the SDP."""
    raise NotImplementedError


@then('there should be a pvc in the SDP namespace')
def _():
    """there should be a pvc in the SDP namespace."""
    raise NotImplementedError