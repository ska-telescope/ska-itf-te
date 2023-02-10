#!/usr/bin/python3
# usage python3 echoTcpServer.py [bind IP]  [bind PORT]

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
outputs = [0]*MAX_OUTPUTS

error_msgs = []
error_pos = -1

CMD_HELP = \
    "SYST:VERS        version\n" \
    "SYST:HELP        help message\n" \
    "SYST:HELP:SYNT   syntax help message\n" \
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


def read_command_system(rcmd):
    """
    Read system command
    """
    global error_pos
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
        if len(error_msgs):
            cmd_resp = "1, %s" % error_msgs[0]
            error_pos = 1
        else:
            cmd_resp = "0, No error"
    elif rcmd[5:] == "ERR:NEXT?":
        if len(error_msgs):
            try:
                cmd_resp = "%s, %s" % (error_pos+1, error_msgs[error_pos])
                error_pos += 1
            except IndexError:
                cmd_resp = ""
                error_pos = 0
                reset_errors()
        else:
            cmd_resp = "0, No error"
    elif rcmd[5:] == "ERR:ALL?":
        n = 0
        cmd_resp = ""
        for error_msg in error_msgs:
            n += 1
            cmd_resp += "%d, %s\n" % (n, error_msg)
    elif rcmd[5:] == "ERR:COUN?":
        cmd_resp = "%d" % len(error_msgs)
    else:
        cmd_resp = "ok"
    return cmd_resp


def read_command_output(rcmd):
    """
    Read output command
    """
    global error_msgs, error_pos, outputs
    cmd_resp = "ok"
    outp_num = int(rcmd[4])
    if outp_num < 1 or outp_num > MAX_OUTPUTS:
        return "Invalid %d" % outp_num
    logging.info("Read input %d", outp_num)
    if rcmd[5:] == "?":
        logging.info("Read input %d", outp_num)
        cmd_resp = str(outputs[outp_num-1])
    elif rcmd[5:] == ":START":
        outputs[outp_num-1] = 1
    elif rcmd[5:] == ":STOP":
        outputs[outp_num-1] = 0
    else:
        error_pos += 1
        error_msgs.append("Invalid output command '%s'" % rcmd)
        cmd_resp = "huh?"
    return cmd_resp



def reset_errors():
    """
    Reset error messages
    """
    global error_msgs, error_pos
    error_pos = 0
    error_msgs.clear()


def reset_outputs():
    """
    Reset outputs to off
    """
    global outputs
    outp_num = 0
    while outp_num < MAX_OUTPUTS:
        outputs[outp_num] = 0
        outp_num += 1

def read_command(rcmd):
    """
    Respond to command
    """
    global error_msgs, outputs
    # TODO add commands
    if rcmd == "HELP":
        cmd_resp = CMD_HELP
    elif rcmd == "*IDN?":
        cmd_resp = IDENTITY
    elif rcmd == "OUTP:PROT:CLE" or rcmd == "ABOR":
        return None
    elif rcmd[0:4] == "SYST":
        cmd_resp = read_command_system(rcmd)
    elif rcmd[0:4] == "OUTP":
        cmd_resp = read_command_output(rcmd)
    elif rcmd == "*RST":
        return "reset"
        clear()
    elif rcmd == "INIT":
        reset_outputs()
    elif rcmd == "*CLS":
        reset_errors()
        reset_outputs()
        cmd_resp = "ok"
    elif rcmd == "*TST?":
        if error_msgs:
            cmd_resp = "Found %d errors" % len(error_msgs)
        else:
            cmd_resp = "All systems go"
    elif rcmd == "*STB?":
        cmd_resp = ""
        for output in outputs:
            cmd_resp += "%d" % output
    else:
        error_msgs.append("Invalid command '%s'" % rcmd)
        cmd_resp = "huh?"
    return cmd_resp


def usage(cmd):
    """
    Help message
    """
    rcmd = os.path.basename(cmd)
    print("Usage:\n\t%s <ADDRESS> [PORT]" % rcmd)
    sys.exit(1)


def main(host, port):
    """
    Listen for incoming connections
    """
    logging.info("Listen on %s:%s", host, port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        retry = 3
        while retry > 0:
            try:
                s.bind((host, port))
                break
            except OSError as e:
                logging.error("%s", str(e))
            retry -= 1
            logging.warning("Retry %d of 3", 3-retry)
            time.sleep(60)
        if retry == 0:
            logging.error("Could not connect")
            return
        logging.info("Listening")
        s.listen()
        conn, addr = s.accept()
        try:
            print(f"Connected by {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                try:
                    rxdata = data.decode("utf-8").strip().upper()
                except UnicodeDecodeError:
                    break
                logging.info("RX> %s", rxdata)
                txdata = read_command(rxdata)
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
            conn.close()


if __name__ == "__main__":  # pragma: no cover
    try:
        HOST = sys.argv[1]
    except IndexError:
        usage(sys.argv[0])
    try:
        PORT = int(sys.argv[2])
    except IndexError:
        PORT = 5025
    LOG_LEVEL = logging.INFO
    logging.basicConfig(level=LOG_LEVEL)
    main(HOST, PORT)
