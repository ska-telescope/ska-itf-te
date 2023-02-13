#!/usr/bin/python3
"""
TCP client
"""

import argparse
import logging
import os
import socket
import sys

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 5302  # The port used by the server
MSG = b""


# pylint: disable-next=too-few-public-methods
class ScpiClient():
    """
    TCP client for SCPI server
    """
    def __init__(self, host, port):
        """
        Get the show on the road
        """
        logging.info("Connect to host %s port %d", host, port)
        self.host = host
        self.port = port

    def send(self, msg):
        """
        Open socket and send message
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_skt:
            try:
                s_skt.connect((self.host, self.port))
            except ConnectionRefusedError:
                logging.error("Connection refused")
                return None
            logging.info("TX> %s", msg)
            txdata = bytes(msg, 'utf-8')
            s_skt.sendall(txdata)
            try:
                data = s_skt.recv(1024)
            except ConnectionResetError:
                logging.error("Connection reset")
                return None
        logging.info("Connected")
        try:
            rxdata = data.decode("utf-8").strip()
        except UnicodeDecodeError:
            logging.error("Invalid data")
        logging.info("Received %d bytes", len(rxdata))
        return rxdata


def usage(cmd):
    """
    Help message
    """
    # pylint: disable-next=unused-variable
    rcmd = os.path.basename(cmd)
    print("Usage:\n\t{rcmd} -n <ADDRESS> -p <PORT> <MESSAGE>")
    sys.exit(1)


def scpi_client_send(host, port, msg):
    """
    The main peanut
    """
    scpi_client = ScpiClient(host, port)
    rx_data = scpi_client.send(msg)
    if rx_data:
        print(rx_data)


if __name__ == "__main__":  # pragma: no cover
    # Read command line
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

    MSG = ' '.join(unknownargs)

    logging.basicConfig(level=LOG_LEVEL)
    scpi_client_send(HOST, PORT, MSG)
