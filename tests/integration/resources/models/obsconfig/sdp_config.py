"""."""
from typing import Any, NamedTuple, Tuple, Union, cast

from ska_tmc_cdm.messages.central_node.sdp import (
    BeamConfiguration,
    ChannelConfiguration,
    EBScanType,
    EBScanTypeBeam,
    ExecutionBlockConfiguration,
    FieldConfiguration,
    PhaseDir,
    PolarisationConfiguration,
    ProcessingBlockConfiguration,
    ScriptConfiguration,
    SDPConfiguration,
)
from ska_tmc_cdm.messages.subarray_node.configure import SDPConfiguration as SDPScanConfiguration

from .base import encoded
from .channelisation import Channelization
from .dishes import Dishes
from .target_spec import ArraySpec, BaseTargetSpec, TargetSpecs


# pylint: disable=invalid-name
# pylint: disable=too-many-ancestors
# pylint: disable=use-dict-literal
class Beamgrouping(NamedTuple):
    """A class representing Beamgrouping."""

    id: str
    configuration: BeamConfiguration
    types: dict[str, EBScanTypeBeam]


DEFAULT_FIELDS = {
    "field_a": FieldConfiguration(
        field_id="field_a",
        pointing_fqdn="...",
        phase_dir=PhaseDir(
            ra=[123.0],
            dec=[-60.0],
            reference_time="2023-02-16T01:23:45.678900",
            reference_frame="ICRF3",
        ),
    )
}

DEFAULT_POLARISATIONS = {
    "all": PolarisationConfiguration(polarisations_id="all", corr_type=["XX", "XY", "YY", "YX"])
}

DEFAULT_BEAMS = {
    "vis0": Beamgrouping(
        "vis0",
        BeamConfiguration(beam_id="vis0", function="visibilities"),
        {
            "default_beam_type": EBScanTypeBeam(
                channels_id="vis_channels", polarisations_id="all"
            ),
            "field_a_beam_type": EBScanTypeBeam(field_id="field_a"),
        },
    ),
}


def DEFAULT_SCAN_TYPES(owner: "ScanTypes"):
    """_summary_.

    :param: owner: _descripttion_
    :return: _description_
    """
    return {
        ".default": EBScanType(
            scan_type_id=".default",
            beams={"vis0": owner.get_beam_configurations("vis0").types["default_beam_type"]},
        ),
        "target:a": EBScanType(
            scan_type_id="target:a",
            beams={"vis0": owner.get_beam_configurations("vis0").types["field_a_beam_type"]},
            derive_from=".default",
        ),
    }


class ScanTypes(TargetSpecs):
    """A class representing scan types."""

    def __init__(
        self,
        additional_beam_groupings: list[Beamgrouping] | None = None,
        additional_scan_types: list[EBScanType] | None = None,
        base_target_specs: dict[str, BaseTargetSpec] | None = None,
        array: ArraySpec | None = None,
    ) -> None:
        """Init object.

        :param: additional_beam_groupings: _description_
        :param: additional_scan_types: _description_
        :param: base_target_specs: _description_
        :param: array: _description_
        """
        TargetSpecs.__init__(self, base_target_specs, array)
        self._beam_configurations = DEFAULT_BEAMS
        self._scan_type_configurations = DEFAULT_SCAN_TYPES(self)

        if additional_beam_groupings is not None:
            self._beam_configurations = {
                **self._beam_configurations,
                **{beam_grouping.id: beam_grouping for beam_grouping in additional_beam_groupings},
            }
        if additional_scan_types is not None:
            self._scan_type_configurations = {
                **self._scan_type_configurations,
                **{
                    additional_scan_type.scan_type_id: additional_scan_type
                    for additional_scan_type in additional_scan_types
                },
            }

        self._pending_scan_type = None

    def add_beam_configuration(
        self,
        config_name: str,
        function: str,
        beam_types: dict[str, EBScanTypeBeam] | None = None,
        search_beam_id: int | None = None,
        timing_beam_id: int | None = None,
        vlbi_beam_id: int | None = None,
    ):
        """Add beam configuration.

        :param: config_name: _description_
        :param: function: _description_
        :param: beam_types: _description_
        :param: search_beam_id: _description_
        :param: timing_beam_id: _description_
        :param: vlbi_beam_id: _description_
        """
        assert (
            self._beam_configurations.get(config_name) is None
        ), f"configuration {config_name} already exists."
        if search_beam_id:
            beam_configuration = BeamConfiguration(
                beam_id=config_name,
                function=function,
                search_beam_id=search_beam_id,
            )
        if timing_beam_id:
            beam_configuration = BeamConfiguration(
                beam_id=config_name,
                function=function,
                timing_beam_id=timing_beam_id,
            )
        if vlbi_beam_id:
            beam_configuration = BeamConfiguration(
                beam_id=config_name,
                function=function,
                vlbi_beam_id=vlbi_beam_id,
            )
        else:
            beam_configuration = BeamConfiguration(beam_id=config_name, function=function)
        if beam_types is None:
            beam_types = dict()
        self._beam_configurations[config_name] = Beamgrouping(
            config_name, beam_configuration, beam_types
        )

    def add_beam_types(self, grouping_id: str, beam_types: dict[str, EBScanTypeBeam]):
        """Add beam types.

        :param: grouping_id: _description_
        :param: beam_types: _description_
        """
        assert self._beam_configurations.get(grouping_id), (
            f"grouping {grouping_id} does not exist, did you call" " `add_beam_configuration()`."
        )
        current_beam_types = self._beam_configurations[grouping_id].types
        current_beam_configuration = self._beam_configurations[grouping_id].configuration
        self._beam_configurations[grouping_id] = Beamgrouping(
            grouping_id,
            current_beam_configuration,
            {**current_beam_types, **beam_types},
        )

    def add_scan_type_configuration(
        self,
        config_name: str,
        beams: Union[
            dict[str, dict[str, EBScanTypeBeam]],
            Tuple[str, str],
            list[Tuple[str, str]],
        ],
        derive_from: str | None = None,
    ):
        """Add scan  type configuration.

        :param: config_name: _description_
        :param: beams: _description_
        :param: derive_from: _description_
        """
        agg_beam_types: dict[str, EBScanTypeBeam] = dict()

        def add_beam(grouping_id: str, beam_type_id: str):
            beam_configuration = self.get_beam_configurations(grouping_id)
            assert beam_configuration, (
                f"Beam grouping {grouping_id} does not exist, did you add a"
                " beam configuration by calling `add_beam_configuration'"
            )
            beam_type = beam_configuration.types.get(beam_type_id)
            assert beam_type, (
                f"Beam type {beam_type_id} does not exist, did you add a beam"
                " configuration by calling `add_beam_configuration'"
            )
            return {grouping_id: beam_type}

        assert (
            self._scan_type_configurations.get(config_name) is None
        ), f"configuration {config_name} already exists."
        if isinstance(beams, dict):
            for beam_grouping_id, beam_types in beams.items():
                beam_grouping = self._beam_configurations.get(beam_grouping_id)
                assert beam_grouping, (
                    f"beam configuration {beam_grouping_id} does not exist,you"
                    " first need to create a beam configuration by calling"
                    " `add_beam_configuration'"
                )
                agg_beam_types = {**agg_beam_types, **beam_types}
        elif isinstance(beams, tuple):
            grouping_id = beams[0]
            beam_type_id = beams[1]
            agg_beam_types = {
                **agg_beam_types,
                **add_beam(grouping_id, beam_type_id),
            }
        else:
            for mapping in beams:
                grouping_id = mapping[0]
                beam_type_id = mapping[1]
                agg_beam_types = {
                    **agg_beam_types,
                    **add_beam(grouping_id, beam_type_id),
                }

        if derive_from is None:
            eb_scan_type = EBScanType(config_name, beams=agg_beam_types)
        else:
            eb_scan_type = EBScanType(config_name, beams=agg_beam_types, derive_from=derive_from)
        self._scan_type_configurations[config_name] = eb_scan_type

    @property
    def target_spec_scan_types(self):
        """Get target spec scan types.

        :return: _description_
        :rtype: _type_
        """
        return {target.scan_type for target in self.target_specs.values()}

    @property
    def scan_types(self):
        """Get scan types.

        :return: _description_
        :rtype: _type_
        """
        unique_keys = self.target_spec_scan_types
        return [self._scan_type_configurations[key] for key in unique_keys]

    @property
    def target_spec_beams(self):
        """Get target spec beams.

        :return: _description_
        :rtype: _type_
        """
        return {key for scan_type in self.scan_types for key in scan_type.beams.keys()}

    @property
    def beams(self):
        """Get beams.

        :return: _description_
        :rtype: _type_
        """
        unique_keys = self.target_spec_beams
        return [
            beam_configuration.configuration
            for beam_configuration in [self._beam_configurations.get(key) for key in unique_keys]
            if beam_configuration
        ]

    @property
    def scan_type_configurations(self):
        """Get scan type configurations.

        :return: _description_
        :rtype: _type_
        """
        return list(self._scan_type_configurations.keys())

    def get_scan_type_configuration(self, config_name: str):
        """Get can type configurations.

        :param: config_name: _description_
        :return: _description_
        :rtype: _type_
        """
        assert (
            self._scan_type_configurations.get(config_name) is not None
        ), f"configuration {config_name} does not exist."
        return self._scan_type_configurations[config_name]

    @property
    def beam_configurations(self):
        """Get beam configurations.

        :return: _description_
        :rtype: _type_
        """
        return list(self._beam_configurations.keys())

    def get_beam_configurations(self, config_name: str):
        """Get beam configurations.

        :param: config_name: _description_
        :return: _description_
        :rtype: _type_
        """
        assert (
            self._beam_configurations.get(config_name) is not None
        ), f"configuration {config_name} does not exist."
        return self._beam_configurations[config_name]

    @property
    def pending_scan_type_id(self):
        """Get pending scan type id.

        :return: _description_
        :rtype: _type_
        """
        return self._pending_scan_type


class Polarisations(TargetSpecs):
    """A class representing polarisations."""

    def __init__(
        self,
        polarizations: list[PolarisationConfiguration] | None = None,
        base_target_specs: dict[str, BaseTargetSpec] | None = None,
        array: ArraySpec | None = None,
    ) -> None:
        """Init object.

        :param: polarizations: _description_
        :param: base_target_specs: _description_
        :param: array: _description_
        """
        TargetSpecs.__init__(self, base_target_specs, array)

        if polarizations is not None:
            self._polarizations = {
                **{
                    additional_polarization.polarisations_id: additional_polarization  # noqa: E501
                    for additional_polarization in polarizations
                },
            }
        else:
            self._polarizations = DEFAULT_POLARISATIONS

    def _get_polarizations_from_target_specs(self):
        unique_keys = {target.polarisation for target in self.target_specs.values()}
        return [self._polarizations[key] for key in unique_keys]

    @property
    def polarizations(self):
        """Get polarizations.

        :return: _description_
        :rtype: _type_
        """
        return self._get_polarizations_from_target_specs()


class Fields(TargetSpecs):
    """A class representing fields."""

    def __init__(
        self,
        field_configurations: list[FieldConfiguration] | None = None,
        base_target_specs: dict[str, BaseTargetSpec] | None = None,
        array: ArraySpec | None = None,
    ) -> None:
        """Init object.

        :param: field_configurations: _description_
        :param: base_target_specs: _description_
        :param: array: _description_
        """
        TargetSpecs.__init__(self, base_target_specs, array)
        if field_configurations is None:
            self._fields = DEFAULT_FIELDS
        else:
            self._fields = {field.field_id: field for field in field_configurations}

    @property
    def fields(self):
        """Get fields.

        :return: _description_
        :rtype: _type_
        """
        return self._get_fields_from_target_specs()

    @property
    def field_configurations(self):
        """Return field configurations.

        :return: _description_
        :rtype: _type_
        """
        return self._fields

    def _get_fields_from_target_specs(self):
        unique_keys = {target.field for target in self.target_specs.values()}
        return [self._fields[key] for key in unique_keys]


class ProcessingSpec(NamedTuple):
    """A class representing processing specs."""

    script: ScriptConfiguration
    parameters: dict[Any, Any] = {
        # makes sure that Configure transitions to READY
        # after 5 seconds of being in CONFIGURING;
        # this is only needed for `test-receive-addresses` script (v0.6.1+)
        "time-to-ready": 5
    }

    def __hash__(self):
        """Return hash.

        :return: _description_
        :rtype: _type_
        """
        return hash(f"{self.script.name}")


DEFAULT_SCRIPT = ScriptConfiguration(
    kind="realtime", name="test-receive-addresses", version="0.6.1"
)


class ProcessingSpecs(TargetSpecs):
    """A class representing processing specs."""

    def __init__(
        self,
        processing_specs: list[ProcessingSpec] | None = None,
        base_target_specs: dict[str, BaseTargetSpec] | None = None,
        array: ArraySpec | None = None,
    ) -> None:
        """Init object.

        :param: processing_specs: _description_
        :param: base_target_specs: _description_
        :param: array: _description_
        """
        TargetSpecs.__init__(self, base_target_specs, array)
        if processing_specs is not None:
            self._processing_specs = {
                **{
                    processing_spec.script.name: processing_spec
                    for processing_spec in processing_specs
                },
            }
        else:
            self._processing_specs = {
                "test-receive-addresses": ProcessingSpec(script=DEFAULT_SCRIPT)
            }

    @property
    def processing_specs(self):
        """Reurn processing specs.

        :return: _description_
        :rtype: _type_
        """
        return self._processing_specs

    @processing_specs.setter
    def processing_specs(self, new_spec: dict[str, ProcessingSpec]):
        """Set processing specs.

        :param: new_spec: _description
        :type new_spec: (dict[str, ProcessingSpec]): _description_
        """
        self._processing_specs = new_spec

    @property
    def target_processings(self):
        """Return target processings.

        :return: _description_
        :rtype: _type_
        """
        return {target.processing for target in self.target_specs.values()}

    @property
    def processing_scripts(self):
        """Return processing scripts.

        :return: _description_
        :rtype: _type_
        """
        unique_keys = self.target_processings
        return [self._processing_specs[key] for key in unique_keys]

    def add_processing_specs(
        self,
        spec_name: str,
        script_version: str,
        script_name: str | None = None,
        script_kind: str = "realtime",
        parameters: dict[Any, Any] | None = None,
    ):
        """Add processing specs.

        :param: spec_name: _description_
        :param: script_version: _description_
        :param: script_name: _description
        :param: script_kind: _description_
        :param: parameters: _description_
        """
        assert (
            self._processing_specs.get(spec_name) is None
        ), f"The processing spec {spec_name}already exists"

        if script_name is None:
            script_name = spec_name

        if parameters is None:
            parameters = {}

        script = ScriptConfiguration(kind=script_kind, name=script_name, version=script_version)
        self._processing_specs[spec_name] = ProcessingSpec(script=script, parameters=parameters)


class ProcessingBlockSpec(ProcessingSpecs):
    """A class representing a processing block."""

    def __init__(
        self,
        processing_specs: list[ProcessingSpec] | None = None,
        base_target_specs: dict[str, BaseTargetSpec] | None = None,
        array: ArraySpec | None = None,
    ) -> None:
        """Init object.

        :param: processing_specs: _description_
        :param: base_target_specs: _description_
        :param: array: _description_
        """
        ProcessingSpecs.__init__(self, processing_specs, base_target_specs, array)

    @property
    def processing_blocks(self):
        """Return processing block configuration.

        :return: _description_
        :rtype: ProcessingBlockConfiguration
        """
        return [
            ProcessingBlockConfiguration(
                pb_id=self.pb_id,
                script=processing_script.script,
                sbi_ids=[self.sbi_id],
                parameters=processing_script.parameters,
            )
            for processing_script in self.processing_scripts
        ]


class ExecutionBlockSpecs(ScanTypes, Channelization, Polarisations, Fields, TargetSpecs):
    """A class representing an execution block."""

    def __init__(
        self,
        context: dict[Any, Any] | None = None,
        max_length: float = 100.0,
        beam_groupings: list[Beamgrouping] | None = None,
        scan_types: list[EBScanType] | None = None,
        channels: list[ChannelConfiguration] | None = None,
        polarizations: list[PolarisationConfiguration] | None = None,
        field_configurations: list[FieldConfiguration] | None = None,
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
        :param: base_target_specs: _description_
        :param: array: _description_
        """
        ScanTypes.__init__(self, beam_groupings, scan_types, base_target_specs, array)
        Channelization.__init__(self, channels)
        Polarisations.__init__(self, polarizations)
        Fields.__init__(self, field_configurations)
        TargetSpecs.__init__(self, base_target_specs, array)
        if context is None:
            context = {}
        self._context = context
        self._max_length = max_length

    @property
    def execution_block(self):
        """Return execution block config.

        :return: _description_
        :rtype: ExecutionBlockConfiguration
        """
        context = self._context
        max_length = self._max_length
        scan_types = self.scan_types
        beams = self.beams
        channels = self.channels
        return ExecutionBlockConfiguration(
            eb_id=self.eb_id,
            context=context,
            max_length=max_length,
            beams=beams,
            scan_types=scan_types,
            channels=channels,
            polarisations=self.polarizations,
            fields=self.fields,
        )


class SdpConfig(Dishes, ExecutionBlockSpecs, ProcessingBlockSpec):
    """A class representing SDP configuration."""

    sdp_assign_resources_schema = "https://schema.skao.int/ska-sdp-assignres/0.4"
    sdp_configure_scan_schema = "https://schema.skao.int/ska-sdp-configure/0.3"

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
        Dishes.__init__(self)
        ExecutionBlockSpecs.__init__(
            self,
            context,
            max_length,
            beam_groupings,
            scan_types,
            channels,
            polarizations,
            field_configurations,
            base_target_specs,
            array,
        )
        ProcessingBlockSpec.__init__(self, processing_specs)

    def _generate_sdp_assign_resources_config(self):
        """Generate sdp assign resources config.

        :return: _description_
        :rtype: _type_
        """
        return SDPConfiguration(
            interface=self.sdp_assign_resources_schema,
            execution_block=self.execution_block,
            resources=cast(dict[Any, Any], self.resource_configuration),
            processing_blocks=self.processing_blocks,
        )

    def _generate_sdp_scan_config(self, target_id: str | None = None):
        """Generate sdp scan config.

        :param: target_id: id of a target
        :type target_id: str
        :return: _description_
        :rtype: _type_
        """
        if target_id:
            assert self.target_specs[target_id], "unknown target id specified"
        else:
            target_id = list(self.target_specs.keys())[0]
        self._pending_scan_type = target_id
        return SDPScanConfiguration(interface=self.sdp_configure_scan_schema, scan_type=target_id)

    def _generate_sdp_run_scan(self):
        """Generate sdp scan config.

        :return: _description_
        :rtype: _type_
        """
        return self.get_scan_id(backwards=True)

    @encoded
    def generate_sdp_run_scan(self):
        """Generate sdp scan config.

        :return: _description_
        :rtype: _type_
        """
        return self._generate_sdp_run_scan()

    @encoded
    def generate_sdp_scan_config(self, target_id: str | None = None):
        """Generate sdp scan config.

        :param: target_id: id of a target
        :type target_id: str
        :return: _description_
        :rtype: _type_
        """
        return self._generate_sdp_scan_config(target_id)

    @encoded
    def generate_sdp_assign_resources_config(self):
        """Generate sdp assign resources config.

        :return: _description_
        :rtype: _type_
        """
        return self._generate_sdp_assign_resources_config()
