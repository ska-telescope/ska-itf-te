#!/usr/bin/python

import getopt
import hvac
import logging
import os
import subprocess
import sys

LOG_LEVEL = logging.DEBUG
logging.basicConfig(level=LOG_LEVEL)
_module_logger = logging.getLogger(__name__)

DEFAULT_URL = "http://127.0.0.1:8200"

class kv1adapter(hvac.adapters.Adapter):

    def __init__(
        self,
        base_uri=DEFAULT_URL,
        token=None,
        cert=None,
        verify=True,
        timeout=30,
        proxies=None,
        allow_redirects=True,
        session=None,
        namespace=None,
        ignore_exceptions=False,
        strict_http=False,
        request_header=True,
    ):
        self.the_token = token
        super().__init__(
            base_uri, token, cert, verify, timeout, proxies, allow_redirects, session,
            namespace, ignore_exceptions, strict_http, request_header
        )

    def get_login_token(self, response):
        _module_logger.info("Read token from '%s'", response)
        return self.the_token

    def request(self, method, url, headers=None, raise_exception=True, **kwargs):
        _module_logger.info("Request")


def usage(p_name: str) -> None:
    print("Usage")
    print(f"\t {p_name} [--host=<VAULT_HOST>] [--path=<VAULT_PATH>]")


def main(y_arg: list) -> int:
    vault_host ="https://vault.skao.int/"
    vault_path = "mid-aa/"
    vault_token = ""

    try:
        opts, _args = getopt.getopt(
            y_arg[1:],
            "hvVH:P:T:",
            [
                "help",
                "host=",
                "path=",
                "token=",
            ]
        )
        _module_logger.info("Read options %s", opts)
    except getopt.GetoptError as opt_err:
        _module_logger.error("Could not read command line: %s", opt_err)
        return 1

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(os.path.basename(y_arg[0]))
            sys.exit(1)
        elif opt in ("-H", "--host"):
            vault_host = arg
        elif opt in ("-P", "--path"):
            vault_path = arg
        elif opt in ("-T", "--token"):
            vault_token = arg
        else:
            _module_logger.error("Invalid option %s", opt)

    _module_logger.info("Start client for %s", vault_host)
    client = hvac.Client(url=vault_host)

    if not client.is_authenticated():
        print(f"Client for host {vault_host} is not authenticated")
        return 1

    _module_logger.info("List path %s", vault_path)
    input_file1 = subprocess.run(["vault", "kv", "list", vault_path], stdout=subprocess.PIPE, text=True)
    print(input_file1.stdout)

    try:
        # adapter = hvac.adapters.Adapter(base_uri=vault_host, token=vault_token)
        adapter = kv1adapter(base_uri=vault_host, token=vault_token)
        kv1 = hvac.api.secrets_engines.KvV1(adapter)
        list_response = kv1.list_secrets(path=vault_path)
        print(f'Secrets in path "{vault_path}" : {list_response}')
        # list_response = client.secrets.kv.v1.list_secrets(path=vault_path)
    except Exception as e:
        _module_logger.error(e)

    # read_response = client.secrets.kv.read_secret_version(path=vault_path)
    # print('Values under path "{the_path}" : {read_response}')

    # list_response = client.secrets.kv.v2.list_secrets(
    #     path=the_path
    # )
    # list_folders = list_response['data']['keys']
    # print(list_folders)


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
