#!/usr/bin/env python
"""Simple SCPI simulator for the Skysim Controller implementation."""
import argparse
import logging
import os
import sys
from socket import gethostname
from typing import Dict, Final, Tuple

from ska_ser_test_equipment.scpi import (
    InterfaceDefinitionFactory,
    ScpiOverTcpSimulator,
    SupportedAttributeType,
)


class SkysimControllerSimulator(ScpiOverTcpSimulator):
    """A concrete simulator class."""

    DEFAULTS: Final[Dict[str, SupportedAttributeType]] = {
        "gaussian_noise_source": False,
        "programmable_attenuator": False,
        "gpio_3": False,
        "gpio_4": False,
        "gpio_5": False,
        "gpio_6": False,
        "gpio_7": False,
    }

    def __init__(
        self,
        address: Tuple[str, int],
        model: str,
        **kwargs: SupportedAttributeType,
    ) -> None:
        """
        Initialise a new instance.

        :param address: address on which to run the server.
        :param model: the model identifier to use
        :param kwargs: initial values for simulator attributes; where an
            initial value is not provided for an attribute, a default
            value will be used.
        :raises NotImplementedError: not yet implement
        """
        logging.info("Initialise skysim controller model %s", model)
        try:
            interface_definition = InterfaceDefinitionFactory()(model)
        except KeyError:
            # pylint: disable-next=raise-missing-from
            raise NotImplementedError("Not part of the current story")

        initial_values = kwargs
        for key, value in self.DEFAULTS.items():
            initial_values.setdefault(key, value)

        super().__init__(address, interface_definition, initial_values)

    def reset(self) -> None:
        """Reset to factory default values."""
        self.set_attribute("gaussian_noise_source", False)
        self.set_attribute("programmable_attenuator", False)
        self.set_attribute("gpio_3", False)
        self.set_attribute("gpio_4", False)
        self.set_attribute("gpio_5", False)
        self.set_attribute("gpio_6", False)
        self.set_attribute("gpio_7", False)


def main(model=None, host=None, port=0) -> int:
    """
    Run the socketserver main loop.

    :param model: test equipment model number
    :param host: name or IP address of server
    :param port: port number to listen on

    :returns: server exit code
    """
    if model is None:
        model = os.getenv("SIMULATOR_MODEL", "SkySimCtl").upper()
    if host is None:
        host = os.getenv("SIMULATOR_HOST", gethostname())
    if port == 0:
        port = int(os.getenv("SIMULATOR_PORT", "5025"))

    logging.debug("Start model %s host %s port %s", model, host, port)
    try:
        server = SkysimControllerSimulator((host, port), model)
    except NotImplementedError as err:
        logging.error("No interface definition for model %s: %s", model, str(err))
        return 1
    except OSError as err:
        logging.error("Could not open server %s:%s <%s>", host, port, str(err))
        return 1
    logging.warning("Start server")
    with server:
        server.serve_forever()
    logging.warning("Done")
    return 0


if __name__ == "__main__":  # pragma: no cover
    RETURN_VALUE = 1
    try:
        LOG_LEVEL = logging.WARNING
        parser = argparse.ArgumentParser()
        parser.add_argument("-m", "--model", help="simulator model")
        parser.add_argument("-n", "--host", help="simulator hostname")
        parser.add_argument("-p", "--port", help="simulator port number")
        parser.add_argument(
            "-i",
            "--info",
            action="store_true",
            help="Set logging level to INFO",
        )
        parser.add_argument(
            "-d",
            "--debug",
            action="store_true",
            help="Set logging level to DEBUG",
        )

        args = parser.parse_args()

        logging.basicConfig(level=LOG_LEVEL)

        logging.debug("args.name=%s", args.model)
        logging.debug("args.host=%s", args.host)
        logging.debug("args.port=%s", args.port)
        if args.port is None:
            PORT = 0
        else:
            PORT = int(args.port)
        if args.debug:
            LOG_LEVEL = logging.DEBUG
        elif args.info:
            LOG_LEVEL = logging.INFO
        else:
            LOG_LEVEL = logging.WARNING

        RETURN_VALUE = main(args.model, args.host, PORT)
    except KeyboardInterrupt:
        logging.error("Interrupted")
        RETURN_VALUE = 1
    sys.exit(RETURN_VALUE)
