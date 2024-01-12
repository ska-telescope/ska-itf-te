#!/usr/bin/python
import os
import sys
import datetime, json
import tango
import getopt
import logging

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger(__name__)
_module_logger.setLevel(logging.WARNING)


def usage(p_name: str) -> None:
    """
    Show how it is done.

    :param p_name: executable name
    """
    print(f"{p_name}")
    print(f"{p_name} --tmc")
    print(f"{p_name} --csp")


def main(y_arg: list) -> int:
    """
    Read and display Tango instances.

    :param y_arg: input arguments
    """
    itype = None
    try:
        opts, _args = getopt.getopt(
            y_arg[1:],
            "vVI:",
            [
                "instance="
            ],
        )
    except getopt.GetoptError as opt_err:
        print(f"Could not read command line: {opt_err}")
        return 1

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(os.path.basename(y_arg[0]))
            sys.exit(1)
        elif opt in ("-A", "--instance"):
            itype = arg.upper()
        elif opt == "-v":
            _module_logger.setLevel(logging.INFO)
        elif opt == "-V":
            _module_logger.setLevel(logging.DEBUG)
        else:
            _module_logger.error("Invalid option %s", opt)

    # Take the namespace name from the deployment job
    # KUBE_NAMESPACE = "ci-ska-mid-itf-at-1702-add-csplmc-tests"
    # CLUSTER_DOMAIN = "miditf.internal.skao.int"
    # set the name of the databaseds service
    # DATABASEDS_NAME = "tango-databaseds"
    # tango_host = f"{DATABASEDS_NAME}.{KUBE_NAMESPACE}.svc.{CLUSTER_DOMAIN}:10000"
    # set the TANGO_HOST
    # os.environ["TANGO_HOST"] = tango_host

    tango_host = os.getenv("TANGO_HOST")
    _module_logger.info("Tango host %s" % tango_host)
    # TIMEOUT=60

    database = tango.Database()
    instance_list = database.get_device_exported("*")
    _module_logger.info(f"{len(instance_list)} device instances available")
    devs = {}
    for instance in instance_list.value_string:
        dev = tango.DeviceProxy(instance)
        devs[instance] = dev

    _module_logger.info("Read %d device instances" % (len(devs)))
    for instance in devs:
        if instance[0:4] == "sys/":
            _module_logger.info(f"Skip {instance}")
            continue
        if itype:
            iupp = instance.upper()
            if itype not in iupp:
                _module_logger.info(f"Ignore {instance}")
                continue
        print("*" * len(instance))
        print(instance)
        print("*" * len(instance))
        dev = devs[instance]
        cmds = dev.get_command_list()
        if 'GetVersionInfo' in cmds:
            verinfo = dev.GetVersionInfo()
            print(f"Version    : {verinfo[0]}")
        print(f"Commands   : {' '.join(cmds)}")
        print()
        if dev.State() == tango._tango.DevState.ON:
            attribs = dev.get_attribute_list()
            # if "obsState" in attribs:
            #   print(f"obs state : {dev.obsState}")
            print("Attributes :")
            for attrib in attribs:
                try:
                    print(f"\t{attrib} : {dev.read_attribute(attrib).value}")
                except Exception:
                    print(f"\t{attrib} could bot be read!")
        elif 'Status' in cmds:
            print(f"status    : {dev.Status()}")
        else:
            pass

        # print(dev.info())

    # CSP = DeviceProxy("mid-csp/control/0")

    # print(f"Admin mode : {CSP.adminmode}")
    # print(f"State      : {CSP.State()}")


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
