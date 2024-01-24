#!/usr/bin/python
"""
Read information about Tango devices.
"""
import getopt
import logging
import os
import sys

from tango_info.get_tango_info import show_attributes, show_commands, show_devices

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger(__name__)
_module_logger.setLevel(logging.WARNING)

KUBE_NAMESPACE = "ci-ska-mid-itf-at-1820-tmc-test-sdp-notebook-v2"
CLUSTER_DOMAIN = "miditf.internal.skao.int"
DATABASEDS_NAME = "tango-databaseds"


def usage(p_name: str) -> None:
    """
    Show how it is done.

    :param p_name: executable name
    """
    print("Display device names only")
    print(f"\t{p_name}")
    print("Display all devices")
    print(f"\t{p_name} [-f]")
    print(f"\t{p_name} -e [-f]")
    print("Filter on device name")
    print(f"\t{p_name} [-f] --device=<DEVICE>")
    print(f"\t{p_name} -e [-f] --device=<DEVICE>")
    print(f"\t{p_name} -q [-f] --device=<DEVICE>")
    print("Filter on attribute name")
    print(f"\t{p_name} -e [-f] --attribute=<ATTRIBUTE>")
    print("where:")
    print("\t-e\tdisplay in markdown format")
    print("\t-q\tdisplay status and name only")
    print("\t-f\tget commands and attributes regadrless of state")
    print(
        "\t--device=<DEVICE>\tdevice name, e.g. 'csp'"
        " (not case sensitive, only a part is needed)"
    )
    print("--attribute=<ATTRIBUTE>\tattribute name, e.g. 'obsState'")


def main(y_arg: list) -> int:  # noqa: C901
    """
    Read and display Tango devices.

    :param y_arg: input arguments
    :return: error condition
    """
    itype: str | None = None
    evrythng: int = 1
    fforce: bool = False
    show_host: bool = False
    tgo_attrib: str | None = None
    tgo_cmd: str | None = None
    try:
        opts, _args = getopt.getopt(
            y_arg[1:],
            "aefhqvVA:C:I:",
            ["help", "device=", "attribute=", "command="],
        )
    except getopt.GetoptError as opt_err:
        print(f"Could not read command line: {opt_err}")
        return 1

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(os.path.basename(y_arg[0]))
            sys.exit(1)
        elif opt in ("-A", "--attribute"):
            tgo_attrib = arg
        elif opt in ("-C", "--command"):
            tgo_cmd = arg
        elif opt in ("-I", "--device"):
            itype = arg.upper()
        elif opt == "-a":
            show_host = True
        elif opt == "-e":
            evrythng = 2
        elif opt == "-f":
            fforce = True
        elif opt == "-q":
            evrythng = 0
        elif opt == "-v":
            _module_logger.setLevel(logging.INFO)
        elif opt == "-V":
            _module_logger.setLevel(logging.DEBUG)
        else:
            _module_logger.error("Invalid option %s", opt)

    tango_host = f"{DATABASEDS_NAME}.{KUBE_NAMESPACE}.svc.{CLUSTER_DOMAIN}:10000"
    if show_host:
        print(f"TANGO_HOST={tango_host}")
        return 0

    os.environ["TANGO_HOST"] = tango_host
    _module_logger.info("Set TANGO_HOST to %s", tango_host)

    if tgo_attrib is not None:
        show_attributes(evrythng, fforce, tgo_attrib)
        return 0

    if tgo_cmd is not None:
        show_commands(evrythng, fforce, tgo_cmd)
        return 0

    show_devices(evrythng, fforce, itype)

    return 0


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
