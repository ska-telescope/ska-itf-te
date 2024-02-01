#!/usr/bin/python
"""
Read information about Tango devices.
"""
import getopt
import logging
import os
import sys

from ska_mid_itf.tango_info.get_tango_info import (
    check_tango, show_attributes, show_command_inputs, show_commands, show_devices
)
from ska_mid_itf.ska_jargon.ska_jargon import print_jargon

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger(__name__)
_module_logger.setLevel(logging.WARNING)

# KUBE_NAMESPACE = "ci-ska-mid-itf-at-1820-tmc-test-sdp-notebook-v2"
KUBE_NAMESPACE = "integration"
CLUSTER_DOMAIN = "miditf.internal.skao.int"
DATABASEDS_NAME = "tango-databaseds"


def usage(p_name: str) -> None:
    """
    Show how it is done.

    :param p_name: executable name
    """
    print("Display Tango database address")
    print(f"\t{p_name} -t [--namespace=<NAMESPACE>|--host=<HOST>]")
    print("Display all devices")
    print(f"\t{p_name} -e|-q|-s [-f] [--namespace=<NAMESPACE>|--host=<HOST>]")
    print("Filter on device name")
    print(
        f"\t{p_name} -e|-q|-s [-f] --device=<DEVICE>"
        " [--namespace=<NAMESPACE>|--host=<HOST>]"
    )
    print("Filter on attribute name")
    print(
        f"\t{p_name} -e|-q|-s [-f] --attribute=<ATTRIBUTE>"
        " [--namespace=<NAMESPACE>|--host=<HOST>]"
    )
    print("Display known acronyms")
    print(f"\t{p_name} -a")
    print("where:")
    print("\t-e\t\t\t\tdisplay in markdown format")
    print("\t-q\t\t\t\tdisplay name, status and query devices")
    print("\t-n\t\t\t\tdisplay name and status only")
    print("\t-f\t\t\t\tget commands and attributes regadrless of state")
    print(
        "\t--device=<DEVICE>\t\tdevice name, e.g. 'csp'"
        " (not case sensitive, only a part is needed)"
    )
    print(
        "\t--namespace=<NAMESPACE>\t\tKubernetes namespace for Tango database,"
        " e.g. 'integration'"
    )
    print("\t--host=<HOST>\t\t\tTango database host and port, e.g. 10.8.13.15:10000")
    print("\t--attribute=<ATTRIBUTE>\t\tattribute name, e.g. 'obsState' (case sensitive)")
    print(
        f"\t--namespace=<NAMESPACE>\t\tKubernetes namespace, default is {KUBE_NAMESPACE}"
    )


def main(y_arg: list) -> int:  # noqa: C901
    """
    Read and display Tango devices.

    :param y_arg: input arguments
    :return: error condition
    """
    global KUBE_NAMESPACE

    itype: str | None = None
    evrythng: int = 1
    fforce: bool = False
    show_jargon: bool = False
    show_tango: bool = False
    tgo_attrib: str | None = None
    tgo_cmd: str | None = None
    tgo_in_type: str | None = None
    tango_host: str | None = None
    try:
        opts, _args = getopt.getopt(
            y_arg[1:],
            "aefhnqtvVA:C:H:D:N:T:",
            ["help", "input", "host=", "device=", "attribute=", "command=", "namespace="],
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
        elif opt in ("-H", "--host"):
            tango_host = arg
        elif opt in ("-D", "--device"):
            itype = arg.upper()
        elif opt in ("-N", "--namespace"):
            KUBE_NAMESPACE = arg
        elif opt in ("-T", "--input"):
            tgo_in_type = arg.lower()
        elif opt == "-a":
            show_jargon = True
        elif opt == "-t":
            show_tango = True
        elif opt == "-e":
            evrythng = 2
        elif opt == "-f":
            fforce = True
        elif opt == "-q":
            evrythng = 3
        elif opt == "-n":
            evrythng = 0
        elif opt == "-v":
            _module_logger.setLevel(logging.INFO)
        elif opt == "-V":
            _module_logger.setLevel(logging.DEBUG)
        else:
            _module_logger.error("Invalid option %s", opt)

    if show_jargon:
        print_jargon()
        return 0

    if tango_host is None:
        tango_fqdn = f"{DATABASEDS_NAME}.{KUBE_NAMESPACE}.svc.{CLUSTER_DOMAIN}"
        tango_host = f"{tango_fqdn}:10000"
    else:
        tango_fqdn = tango_host.split(":")[0]

    if show_tango:
        check_tango(tango_fqdn)
        return 0

    os.environ["TANGO_HOST"] = tango_host
    _module_logger.info("Set TANGO_HOST to %s", tango_host)

    if tgo_attrib is not None:
        show_attributes(evrythng, fforce, tgo_attrib)
        return 0

    if tgo_cmd is not None:
        show_commands(evrythng, fforce, tgo_cmd)
        return 0

    if tgo_in_type is not None:
        show_command_inputs(tango_host, tgo_in_type)
        return 0

    show_devices(evrythng, fforce, itype)

    return 0


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
