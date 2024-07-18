"""Pytest fixtures and bdd step implementations specific to tmc integration tests."""

import os
import pytest

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from .. import conftest


@pytest.fixture(name="set_up_subarray_log_checking_for_tmc")
def fxt_set_up_log_capturing_for_cbf(
    log_checking: fxt_types.log_checking,
    sut_settings: conftest.SutTestSettings,
):
    """Set up log capturing (if enabled by CATPURE_LOGS).

    :param log_checking: The skallop log_checking fixture to use
    :param sut_settings: A class representing the settings for the system under test.
    """
    index = sut_settings.subarray_id
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        subarray = str(tel.tm.subarray(index))
        sdp_subarray1 = str(tel.sdp.subarray(index))
        if tel.skamid:
            subarray_ln = str(tel.skamid.tm.subarray(index).sdp_leaf_node)
            log_checking.capture_logs_from_devices(subarray, sdp_subarray1, subarray_ln)
        else:
            subarray_ln = str(tel.skalow.tm.subarray(index).sdp_leaf_node)
            log_checking.capture_logs_from_devices(subarray, sdp_subarray1, subarray_ln)


# scan configurations


@pytest.fixture(name="base_configuration")
def fxt_sdp_base_configuration(tmp_path) -> conf_types.ScanConfiguration:
    """Set up a base scan configuration to use for sdp.

    :param tmp_path: a temporary path for sending configuration as a file.
    :return: the configuration settings.
    """
    configuration = conf_types.ScanConfigurationByFile(
        tmp_path, conf_types.ScanConfigurationType.STANDARD
    )
    return configuration
