"""."""

import json
from typing import Any, cast

from ska_tmc_cdm.messages.central_node.assign_resources import AssignResourcesRequest
from ska_tmc_cdm.messages.subarray_node.configure import ConfigureRequest

from .base import encoded
from .csp import CSPconfig
from .dishes import Dishes
from .sdp_config import (
    ArraySpec,
    BaseTargetSpec,
    Beamgrouping,
    ChannelConfiguration,
    EBScanType,
    FieldConfiguration,
    PolarisationConfiguration,
    ProcessingSpec,
    SdpConfig,
)
from .tmc_config import TmcConfig

# pylint: disable=no-member
# pylint: disable=too-many-ancestors


class Observation(SdpConfig, CSPconfig, Dishes, TmcConfig):
    """A class representing an observation."""

    def __init__(
        self,
        context: dict[Any, Any] | None = None,
        max_length: float = 100.0,
        beam_groupings: list[Beamgrouping] | None = None,
        scan_types: list[EBScanType] | None = None,
        channels: list[ChannelConfiguration] | None = None,
        polarizations: list[PolarisationConfiguration] | None = None,
        field_configurations: list[FieldConfiguration] | None = None,
        processing_specs: list[ProcessingSpec] | None = None,
        base_target_specs: dict[str, BaseTargetSpec] | None = None,
        array: ArraySpec | None = None,
    ) -> None:
        """Init object.

        :param: context: _description_
        :param: max_length: _description_
        :param: beam_groupings: _description_
        :param: scan_types: _description_
        :param: channels: _description_
        :param: polarizations: _description_
        :param: field_configurations: _description_
        :param: processing_specs: _description_
        :param: base_target_specs: _description_
        :param: array: _description_
        """
        SdpConfig.__init__(
            self,
            context,
            max_length,
            beam_groupings,
            scan_types,
            channels,
            polarizations,
            field_configurations,
            processing_specs,
            base_target_specs,
            array,
        )
        CSPconfig.__init__(self, base_target_specs, array)
        Dishes.__init__(self, base_target_specs, array)
        TmcConfig.__init__(self)

    assign_resources_schema = "https://schema.skao.int/ska-tmc-assignresources/2.1"

    def _generate_assign_resources_config(self, subarray_id: int = 1):
        assign_request = AssignResourcesRequest(
            subarray_id=subarray_id,
            dish=self.dish_allocation,
            sdp_config=self.generate_sdp_assign_resources_config().as_object,
            interface=self.assign_resources_schema,
        )
        return assign_request

    low_assign_resources_schema = "https://schema.skao.int/ska-low-tmc-assignresources/3.0"

    def _generate_low_assign_resources_config(self, subarray_id: int = 1):
        transaction_id = "txn-....-00001"
        assign_request = AssignResourcesRequest(
            interface=self.low_assign_resources_schema,
            transaction_id=transaction_id,
            subarray_id=subarray_id,
            sdp_config=self.generate_sdp_assign_resources_config().as_object,
        )
        return assign_request

    def _generate_scan_config(self, target_id: str | None = None, scan_duration: float = 6):
        if target_id is None:
            target_id = self.next_target_id
        return ConfigureRequest(
            pointing=self.get_pointing_configuration(target_id),
            dish=self.get_dish_configuration(target_id),
            sdp=self.generate_sdp_scan_config(target_id).as_object,
            csp=self.generate_csp_scan_config(target_id).as_object,
            tmc=self.generate_tmc_scan_config(scan_duration),
        )

    @encoded
    def generate_assign_resources_config(self, subarray_id: int = 1):
        """Generate assign resources config.

        :param: subarray_id: id of the subarray
        :return: _description_
        :rtype: _type_
        """
        return self._generate_assign_resources_config(subarray_id)

    def generate_release_all_resources_config_for_central_node(self, subarray_id: int = 1) -> str:
        """Generate release all resources config for central node.

        :param: subarray_id: id of the subarray
        :return: configuration
        :rtype: str
        """
        config = {
            "interface": ("https://schema.skao.int/ska-tmc-releaseresources/2.1"),
            "transaction_id": "txn-....-00001",
            "subarray_id": subarray_id,
            "release_all": True,
            "receptor_ids": [],
        }

        return json.dumps(config)

    @encoded
    def generate_scan_config(self, target_id: str | None = None, scan_duration: float = 6):
        """Generate scan config.

        :param: target_id: id of the target
        :param: scan_duration: duration of the scan
        :return: _description_
        :rtype: _type_
        """
        return self._generate_scan_config(target_id, scan_duration)

    @encoded
    def generate_run_scan_conf(self, backwards: bool = False):
        """Generate run scan config.

        :param: backwards: _description_
        :return: _description_
        :rtype: _type_
        """
        return self.get_scan_id(backwards)

    def generate_scan_config_parsed_for_csp(
        self,
        target_id: str | None = None,
        subarray_id: int = 1,
        scan_duration: float = 4,
    ) -> str:
        """Generate scan config parsed for csp.

        :param: target_id: if of a target
        :param: subarray_id: id of a subarray
        :param: scan_duration: duration of a scan
        :return: csp configuration
        :rtype: str
        """
        config = cast(
            dict[str, Any],
            self.generate_scan_config(target_id, scan_duration).as_dict,
        )
        csp_config = config["csp"]
        csp_config["pointing"] = config["pointing"]
        return json.dumps(csp_config)
