"""
This subpackage provides SCPI support.

It is implemented as a three-layer stack:

* The bottom layer works with SCPI byte strings;

* The middle layer works with device-dependent SCPI queries, commands
  and set operations;

* The top layer works with device-independent attribute queries,
  commands and set operations.

The mapping from device-independent attributes to device-dependent SCPI
fields is intended to be specified in a YAML file. For example, the
YAML file for a Tektronix TSG4014A signal generator:

.. literalinclude:: tektronix_tsg4104a.yaml
   :language: yaml

YAML specification files are registered with the
:py:class:`.InterfaceDefinitionFactory` class, which can then be used to
access them:

.. code-block:: python

   interface_definition_factory = InterfaceDefinitionFactory()
   interface_definition = interface_definition_factory("TSG4101A")

The following module diagram shows decomposition and "uses"
relationships. Though it might not appear layered at first glance, it
shows

* a client stack in which each layer uses only its own layer and the
  layer immediately *below*;

* a server stack in which each layer uses only its own layer and the
  layer immediately *above*.

:py:class:`.InterfaceDefinitionFactory` (not shown) cross-cuts the top
two layers of both stacks.)

.. image:: scpi.png
"""
__all__ = [
    "AttributeClient",
    "AttributeRequest",
    "AttributeResponse",
    "AttributeServerProtocol",
    "ScpiBytesClientFactory",
    "ScpiBytesClientProtocol",
    "ScpiBytesServer",
    "SupportedProtocol",
    "AttributeDefinitionType",
    "InterfaceDefinitionFactory",
    "InterfaceDefinitionType",
    "ScpiClient",
    "ScpiRequest",
    "ScpiResponse",
    "ScpiServer",
    "SupportedAttributeType",
    "ScpiOverTcpSimulator",
]

from ska_ser_test_equipment.scpi.attribute_client import AttributeClient
from ska_ser_test_equipment.scpi.attribute_payload import AttributeRequest, AttributeResponse
from ska_ser_test_equipment.scpi.attribute_server import AttributeServerProtocol
from ska_ser_test_equipment.scpi.bytes_client import (
    ScpiBytesClientFactory,
    ScpiBytesClientProtocol,
    SupportedProtocol,
)
from ska_ser_test_equipment.scpi.bytes_server import ScpiBytesServer
from ska_ser_test_equipment.scpi.interface_definition import (
    AttributeDefinitionType,
    InterfaceDefinitionType,
    SupportedAttributeType,
)
from ska_ser_test_equipment.scpi.scpi_client import ScpiClient
from ska_ser_test_equipment.scpi.scpi_over_tcp_simulator import ScpiOverTcpSimulator
from ska_ser_test_equipment.scpi.scpi_payload import ScpiRequest, ScpiResponse
from ska_ser_test_equipment.scpi.scpi_server import ScpiServer


from ska_skysim_controller.scpi.interface_definition import InterfaceDefinitionFactory
