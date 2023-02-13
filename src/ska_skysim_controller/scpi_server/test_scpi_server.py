#!/usr/bin/python3

import os
import datetime
import sys
import argparse
import logging
from collections import OrderedDict

from ska_skysim_controller.scpi_server.scpi_client import ScpiClient

# Test cases
MSG_RESP = OrderedDict()
MSG_RESP["HELP"] = "Send SYST:HELP for help"
MSG_RESP["*IDN?"] = "Skysim controller 0.0.1"
MSG_RESP["*CLS"] = "ok"
MSG_RESP["INIT"] = "ok"
MSG_RESP["*TST?"] = "All systems go"
MSG_RESP["SYST:VERS"] = "0.0.1"
MSG_RESP["SYST:CTYP"] = "Skysim controller 0.0.1"
MSG_RESP["SYST:DATE"] = datetime.datetime.now().strftime("%Y-%m-%d")
MSG_RESP["SYST:ERR?"] = "0, No error"
MSG_RESP["OUTP1:START"] = "ok"
MSG_RESP["OUTP1?"] = "1"
MSG_RESP["OUTP1:STOP"] = "ok"
MSG_RESP["OUTP2:START"] = "ok"
MSG_RESP["OUTP2?"] = "1"
MSG_RESP["OUTP2:STOP"] = "ok"
MSG_RESP["OUTP3:START"] = "ok"
MSG_RESP["OUTP3?"] = "1"
MSG_RESP["OUTP3:STOP"] = "ok"
MSG_RESP["OUTP4:START"] = "ok"
MSG_RESP["OUTP4?"] = "1"
MSG_RESP["OUTP4:STOP"] = "ok"
MSG_RESP["OUTP5:START"] = "ok"
MSG_RESP["OUTP5?"] = "1"
MSG_RESP["OUTP5:STOP"] = "ok"
MSG_RESP["OUTP6:START"] = "ok"
MSG_RESP["OUTP6?"] = "1"
MSG_RESP["OUTP6:STOP"] = "ok"
MSG_RESP["OUTP7:START"] = "ok"
MSG_RESP["OUTP7?"] = "1"
MSG_RESP["OUTP7:STOP"] = "ok"
MSG_RESP["OUTP8:START"] = "ok"
MSG_RESP["OUTP8?"] = "1"
MSG_RESP["OUTP8:STOP"] = "ok"
MSG_RESP["*STB?"] = "00"
MSG_RESP["test this"] = "huh?"
MSG_RESP["SYST:ERR:ALL?"] = "1, Invalid command 'TEST THIS'"
MSG_RESP["SYST:ERR:COUN?"] = "1"


def usage(cmd):
    """
    Help message
    """
    rcmd = os.path.basename(cmd)
    print("Usage:\n\t%s -n <ADDRESS> [-p PORT]" % rcmd)
    print("\t%s -host=<ADDRESS> [--port=<PORT>]" % rcmd)
    sys.exit(1)


def main(host, port):
    """
    Do the thing.
    """
    # Connect
    err_count = 0
    scpi_client = ScpiClient(host, port)
    # Run test cases
    logging.info("Run %d tests", len(MSG_RESP))
    for msg in MSG_RESP:
        logging.info("TX> %s", msg)
        rx_data = scpi_client.send(msg)
        if rx_data:
            logging.info("RX> %s", rx_data)
            if rx_data == MSG_RESP[msg]:
                logging.info("OK")
            else:
                logging.warning("Response should be '%s'", MSG_RESP[msg])
                err_count += 1
        else:
            logging.warning("No data received")
            err_count += 1
    if err_count:
        print("Test failed: %d errors" % err_count)
        return 1
    print("Test passed")
    return 0


if __name__ == "__main__":  # pragma: no cover
    """
    Read command line
    """
    LOG_LEVEL = logging.WARNING
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--host", help="SCPI device hostname")
    parser.add_argument("-p", "--port", help="SCPI device port number")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Set logging level to INFO",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Set logging level to DEBUG",
    )

    args, unknownargs = parser.parse_known_args()
    if args.host is None:
        usage(sys.argv[0])
    HOST = args.host
    if args.port is None:
        PORT = 5302
    else:
        PORT = int(args.port)
    if args.debug:
        LOG_LEVEL = logging.DEBUG
    elif args.verbose:
        LOG_LEVEL = logging.INFO
    else:
        LOG_LEVEL = logging.WARNING

    logging.basicConfig(level=LOG_LEVEL)
    test_result = main(HOST, PORT)
    sys.exit(test_result)
