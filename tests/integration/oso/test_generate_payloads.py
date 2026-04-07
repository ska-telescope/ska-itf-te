"""."""

from ska_oso_scripting import api
from ska_oso_scripting.pdm_transforms import (
    create_cdm_assign_resources_request_from_scheduling_block,
    create_cdm_configure_requests_from_scheduling_block,
)
from ska_oso_scripting.api.functional.devicecontrol.subarray_control import get_scan_command
import os

# Mock vars
os.environ["EB_ID"] = "eb-986-20260218-6tmxr3kxn4c"
os.environ["SKUID_URL"] = "http://localhost:4000/no/where"

# Load Scheduling Block Definition
sbd = api.load_sbd("tests/integration/resources/sbds/test_sbd.json")


def generate_assign_resources_tmc_payload():
    """_summary_.

    :return: _description_
    :rtype: _type_
    """
    assign_resources = create_cdm_assign_resources_request_from_scheduling_block(
        subarray_id=1, sbd=sbd
    )
    return assign_resources.model_dump_json(indent=2)


def generate_configure_tmc_payloads():
    """_summary_.

    :return: _description_
    :rtype: _type_
    """
    configure = create_cdm_configure_requests_from_scheduling_block(sbd=sbd)
    configure_payloads = []
    for scan_idx, requests in configure.items():
        for req_idx, request in enumerate(requests):
            configure_payloads.append(request.model_dump_json(indent=2))
    return configure_payloads


if __name__ == "__main__":
    # Show Assign Resources payload and configure payloads that would be generated from the test SBD, as well as a scan command for the first scan in the SBD. This is not a test of the correctness of these payloads, but just a demonstration of how to use the wrapper functions to generate them.
    assign_resources_payload = generate_assign_resources_tmc_payload()
    print("Assign Resources payload:")
    print(assign_resources_payload)

    # Show Configure payloads for each scan in the SBD
    configure_payloads = generate_configure_tmc_payloads()
    for idx, payload in enumerate(configure_payloads):
        print(f"Configure payload {idx}:")
        print(payload)

    # Show scan command for the first scan in the SBD
    subarray_id = 1
    scan_command = get_scan_command(subarray_id=subarray_id)
    print(scan_command)
