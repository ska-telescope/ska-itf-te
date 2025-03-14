"""Configure subarray feature tests."""

import logging

import pytest
from pytest_bdd import scenario

logger = logging.getLogger(__name__)


@pytest.mark.skip
@pytest.mark.csp_related
@pytest.mark.skamid
@pytest.mark.scan
@pytest.mark.csp
@scenario("features/csp_configure_scan.feature", "Abort configuring")
def test_abort_configuring(set_up_subarray_log_checking_for_csp: None):
    """Abort scanning.

    :param: set_up_subarray_log_checking_for_csp: sets up subarray log checking for csp
    """


@pytest.mark.csp_related
@pytest.mark.skamid
@pytest.mark.csp
@pytest.mark.configure
@pytest.mark.skip(reason="Skip failing test")  # TEMP COMMIT
@scenario("features/csp_configure_scan.feature", "Configure scan on csp subarray in mid")
def test_configure_csp_mid_subarray():
    """Configure CSP mid subarray."""
