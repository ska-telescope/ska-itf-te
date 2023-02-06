"""
This module implements SCPI interface definition handling.

Interfaces definitions are primarily mappings from instrument-
independent attributes like "frequency" to instrument-specific SCPI
fields like "FREQ".
"""
import logging
import pkgutil
from typing import Dict, TypedDict, Union

import yaml

SupportedAttributeType = Union[bool, float, str]


AttributeDefinitionType = TypedDict(
    "AttributeDefinitionType",
    {
        "field": str,
        "type": str,
        "min_value": float,
        "max_value": float,
        "absolute_resolution": float,
        "bit": int,
        "value": SupportedAttributeType,
    },
    total=False,
)


InterfaceDefinitionType = TypedDict(
    "InterfaceDefinitionType",
    {
        "model": str,
        "supports_chains": bool,
        "poll_rate": float,
        "timeout": float,
        "attributes": Dict[str, AttributeDefinitionType],
    },
)


class InterfaceDefinitionFactory:  # pylint: disable=too-few-public-methods
    """Factory that returns a SCPI interface definition for a given model."""

    def __init__(self) -> None:
        """Initialise a new instance."""
        self._interfaces = {
            "SMB100A": "signal_generator/rohde_and_schwarz_smb100a.yaml",
            "TGR2051": "signal_generator/aimtti_tgr2051.yaml",
            "TSG4104A": "signal_generator/tektronix_tsg4104a.yaml",
            "SPECMON26B": "spectrum_analyser/tektronix_specmon26b.yaml",
            "MS2090A": "spectrum_analyser/anritsu_ms2090a.yaml",
            "SKYSIMCTL": "sky_simulator_controller/sky_sim_ctl.yaml",
        }

    def __call__(self, model: str) -> InterfaceDefinitionType:
        """
        Get an interface definition for the specified model.

        :param model: the name of the model for which an interface
            definition is required.

        :return: SCPI interface definition for the model
        """
        logging.warning("Model set to %s", model)
        file_name = self._interfaces[model]
        interface_definition_data = pkgutil.get_data(
            "ska_ser_test_equipment", file_name
        )
        assert interface_definition_data is not None  # for the type-checker
        interface_definition: InterfaceDefinitionType = yaml.safe_load(
            interface_definition_data
        )
        return interface_definition
