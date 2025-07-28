"""."""

import logging
import os

import pytest

logger = logging.getLogger(__name__)


# TODO: Consider removing this e.g. read from config file or feature file
@pytest.fixture(scope="session")
def settings():
    """Fixture for generating settings to be used in the test.

    :return: _description_
    :rtype: _type_
    """
    settings = {}
    settings["sut_cluster_domain"] = os.getenv("SUT_CLUSTER_DOMAIN")
    settings["SUT_namespace"] = os.getenv("KUBE_NAMESPACE")
    settings["data_dir"] = ".jupyter-notebooks/data/mid_telescope"
    settings["TMC_configs"] = f"{settings['data_dir']}/tmc"
    settings["expected_k_value"] = 1
    settings["override_scan_duration"] = os.getenv("OVERRIDE_SCAN_DURATION")
    settings["override_scan_band"] = os.getenv("OVERRIDE_SCAN_BAND")
    settings["integration_factor"] = os.getenv("INTEGRATION_FACTOR")
    sim_mode = os.getenv("SIM_MODE", "false").lower()
    if sim_mode in ["false", "0", ""]:
        settings["sim_mode"] = False
    elif sim_mode in ["true", "1"]:
        settings["sim_mode"] = True
    else:
        logger.error("SIM_MODE is invalid")
        pytest.fail("SIM_MODE not correctly specified")
    settings["generate_sequence_diagram"] = (
        os.getenv("GENERATE_SEQUENCE_DIAGRAM", "false").lower() == "true"
    )
    settings["artifact_dir"] = "config"
    settings["dish_ids"] = os.getenv("DISH_IDS", "SKA001 SKA036 SKA063 SKA100")

    return settings


# TODO: Consider removing this e.g. read from config file or feature file
@pytest.fixture(scope="session")
def receptor_ids(settings):
    """Fixture for generating list of receptors to be used in test.

    :param settings: _description_
    :return: List of receptor IDs
    :rtype: _type_
    """
    receptors = [dish_id.strip() for dish_id in settings["dish_ids"].split()]
    return receptors
