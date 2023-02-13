#!/usr/bin/python3

import argparse
import os
import socket
import sys
import string
import logging
import time
from datetime import datetime

# from ska_skysim_controller.scpi_server import __version__ as version
VERSION = "0.0.1"
IDENTITY = "Skysim controller %s" % VERSION
MAX_OUTPUTS = 8

CMD_HELP = \
    "SYST:VERS        version\n" \
    "SYST:HELP        help message\n" \
    "SYST:HELP:SYNT   syntax help message\n" \
    "SYST:DATE        current date\n" \
    "SYST:TIME        current time\n" \
    "SYST:CTYP        card destination (identity)\n" \
    "SYST:ERR?        first error\n" \
    "SYST:ERR:NEXT?   next error\n" \
    "SYST:ERR:ALL?    all errors\n" \
    "SYST:ERR:COUN?   number of errors\n" \
    "*IDN?            identify\n" \
    "*RST             reset\n" \
    "INIT             initialize\n" \
    "*CLS             clear status\n" \
    "OUTP1:START      output 1 on\n" \
    "OUTP1:STOP       output 1 off\n" \
    "OUTP1?           output 1 query\n" \
    "*STB?            status byte query\n" \
    "*TST?            self-test"


class ScpiServer(object):
    """
    Read SCPI commands from TCP socket
    """

    def __init__(self, host, port):
        self.outputs = [0]*MAX_OUTPUTS
        self.error_msgs = []
        self.error_pos = -1
        self.host = host
        self.port = port

    def read_command_system(self, rcmd):
        """
        Read system command
        """
        cmd_resp = "ok"
        if rcmd[5:] == "VERS":
            cmd_resp = VERSION
        elif rcmd[5:] == "HELP":
            cmd_resp = CMD_HELP
        elif rcmd[5:] == "HELP:SYNT":
            cmd_resp = CMD_HELP
        elif rcmd[5:] == "CTYP":
            cmd_resp = IDENTITY
        elif rcmd[5:] == "DATE":
            now = datetime.now()
            cmd_resp = now.strftime("%Y-%m-%d")
        elif rcmd[5:] == "TIME":
            now = datetime.now()
            cmd_resp = now.strftime("%H:%M:%S")
        elif rcmd[5:] == "ERR?":
            if len(self.error_msgs):
                cmd_resp = "1, %s" % self.error_msgs[0]
                self.error_pos = 1
            else:
                cmd_resp = "0, No error"
        elif rcmd[5:] == "ERR:NEXT?":
            if len(self.error_msgs):
                try:
                    cmd_resp = "%s, %s" \
                        % (self.error_pos+1, self.error_msgs[self.error_pos])
                    self.error_pos += 1
                except IndexError:
                    cmd_resp = ""
                    self.error_pos = 0
                    self.reset_errors()
            else:
                cmd_resp = "0, No error"
        elif rcmd[5:] == "ERR:ALL?":
            n = 0
            cmd_resp = ""
            for error_msg in self.error_msgs:
                n += 1
                cmd_resp += "%d, %s\n" % (n, error_msg)
        elif rcmd[5:] == "ERR:COUN?":
            cmd_resp = "%d" % len(self.error_msgs)
        else:
            cmd_resp = "ok"
        return cmd_resp


    def read_command_output(self, rcmd):
        """
        Read output command
        """
        cmd_resp = "ok"
        outp_num = int(rcmd[4])
        if outp_num < 1 or outp_num > MAX_OUTPUTS:
            return "Invalid %d" % outp_num
        logging.info("Read input %d", outp_num)
        if rcmd[5:] == "?":
            logging.info("Read input %d", outp_num)
            cmd_resp = str(self.outputs[outp_num-1])
        elif rcmd[5:] == ":START":
            self.outputs[outp_num-1] = 1
        elif rcmd[5:] == ":STOP":
            self.outputs[outp_num-1] = 0
        else:
            self.error_pos += 1
            self.error_msgs.append("Invalid output command '%s'" % rcmd)
            cmd_resp = "huh?"
        return cmd_resp

    def reset_errors(self):
        """
        Reset error messages
        """
        self.error_pos = 0
        self.error_msgs.clear()

    def reset_outputs(self):
        """
        Reset outputs to off
        """
        outp_num = 0
        while outp_num < MAX_OUTPUTS:
            self.outputs[outp_num] = 0
            outp_num += 1

    def status_byte(self):
        bstr = ""
        for output in reversed(self.outputs):
            bstr += "%d" % output
        sbyte = int(bstr, 2)
        return sbyte

    def read_command(self, rcmd):
        """
        Respond to command
        """
        # TODO add commands
        if rcmd == "HELP":
            cmd_resp = "Send SYST:HELP for help"
        elif rcmd == "*IDN?":
            cmd_resp = IDENTITY
        elif rcmd == "OUTP:PROT:CLE" or rcmd == "ABOR":
            return None
        elif rcmd[0:4] == "SYST":
            cmd_resp = self.read_command_system(rcmd)
        elif rcmd[0:4] == "OUTP":
            cmd_resp = self.read_command_output(rcmd)
        elif rcmd == "*RST":
            # self.reset_outputs()
            return "reset"
        elif rcmd == "INIT":
            self.reset_outputs()
            cmd_resp = "ok"
        elif rcmd == "*CLS":
            self.reset_errors()
            self.reset_outputs()
            cmd_resp = "ok"
        elif rcmd == "*TST?":
            if self.error_msgs:
                cmd_resp = "Found %d errors" % len(self.error_msgs)
            else:
                cmd_resp = "All systems go"
        elif rcmd == "*STB?":
            cmd_resp = "%02X" % self.status_byte()
        else:
            self.error_msgs.append("Invalid command '%s'" % rcmd)
            cmd_resp = "huh?"
        return cmd_resp

    def run(self):
        """
        Run the thing
        """
        logging.info("Listen on %s:%s", self.host, self.port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            retry = 3
            while retry > 0:
                try:
                    s.bind((self.host, self.port))
                    break
                except OSError as e:
                    logging.error("%s", str(e))
                retry -= 1
                logging.warning("Retry %d of 3", 3-retry)
                time.sleep(60)
            if retry == 0:
                logging.error("Could not connect")
                return
            while True:
                logging.info("Listening")
                s.listen()
                try:
                    conn, addr = s.accept()
                except KeyboardInterrupt:
                    logging.warning("Interrupted")
                    return
                try:
                    logging.info("Connected by %s", str(addr))
                    data = conn.recv(1024)
                    if not data:
                        break
                    try:
                        rxdata = data.decode("utf-8").strip().upper()
                    except UnicodeDecodeError:
                        break
                    logging.info("RX> %s", rxdata)
                    txdata = self.read_command(rxdata)
                    if txdata is None:
                        logging.error("Error condition")
                        conn.close()
                        return
                    logging.info("TX> %s", txdata)
                    txdata += "\r\n"
                    conn.sendall(bytes(txdata, "utf-8"))
                    if txdata[0:5] == "reset":
                        logging.warning("Shutting down")
                        conn.close()
                        return
                except KeyboardInterrupt:
                    logging.warning("Done")
                finally:
                    logging.warning("Close socket")
                    conn.close()


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
    Listen for incoming connections
    """
    scpi_svr = ScpiServer(host, port)
    scpi_svr.run()


if __name__ == "__main__":  # pragma: no cover
    """
    Read command line
    """
    LOG_LEVEL = logging.INFO
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--host", help="SCPI simulator hostname")
    parser.add_argument("-p", "--port", help="SCPI simulator port number")
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
    HOST = args.host
    if args.host is None:
        usage(sys.argv[0])
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
    main(HOST, PORT)
