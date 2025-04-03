#!/usr/bin/python

import getopt
import hvac
import json
import logging
import os
import subprocess
import sys
import yaml

LOG_LEVEL = logging.WARNING
logging.basicConfig(level=LOG_LEVEL)
_module_logger = logging.getLogger(__name__)

DEFAULT_URL = "http://127.0.0.1:8200"
MID_AIV_MOUNTS = ["cubbyhole/", "dev/", "mid-aa/", "mid-itf/", "shared/"]
DATA_PATH = "tmp/vault"
DATA_FORMATS = ["yaml", "json"]
DEFAULT_DATA_FORMAT = "yaml"


class kv1adapter(hvac.adapters.Adapter):
    """
    Nothing to see here.
    """


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
        """
        Nothing to see here.
        """
        self.the_token = token
        super().__init__(
            base_uri, token, cert, verify, timeout, proxies, allow_redirects, session,
            namespace, ignore_exceptions, strict_http, request_header
        )

    def get_login_token(self, response):
        """
        Nothing to see here.
        """
        _module_logger.info("Read token from '%s'", response)
        return self.the_token

    def request(self, method, url, headers=None, raise_exception=True, **kwargs):
        """
        Nothing to see here.
        """
        _module_logger.info(
            "Request method %s url %s headers %s kwargs %s",
            method,
            url,
            headers,
            kwargs
        )



def list_secrets():
    """
    Nothing to see here.
    """
    # read_response = client.secrets.kv.read_secret_version(path=vault_path)
    # print('Values under path "{the_path}" : {read_response}')

    # list_response = client.secrets.kv.v2.list_secrets(
    #     path=the_path
    # )
    # list_folders = list_response['data']['keys']
    # print(list_folders)

    # try:
    #     # adapter = hvac.adapters.Adapter(base_uri=vault_host, token=vault_token)
    #     adapter = kv1adapter(base_uri=vault_host, token=vault_token)
    #     kv1 = hvac.api.secrets_engines.KvV1(adapter)
    #     list_response = kv1.list_secrets(path=vault_path)
    #     print(f'Secrets in path "{vault_path}" : {list_response}')
    #     # list_response = client.secrets.kv.v1.list_secrets(path=vault_path)
    # except Exception as e:
    #     _module_logger.error(e)
    return


def read_secret_values(
    secret_path: str,
    mval: str,
    secret_data: str,
    data_format: str,
) -> int:
    """
    Read secret values.

    :param secret_path: where to write secrets
    :param data_format: format, i.e. yaml or json
    :returns: error code
    """
    _module_logger.debug("Secret values path %s: %s", secret_path, mval)
    values_path = os.path.join(secret_path, mval)
    try:
        os.makedirs(values_path)
    except FileExistsError:
        pass
    values_file = os.path.join(values_path, "values.yml")
    _module_logger.info("Write values file %s", values_file)
    if data_format == "yaml":
        values_dict = yaml.safe_load(secret_data)
    elif data_format == "yaml":
        values_dict = json.loads(secret_data)
    else:
        _module_logger.error("Format %s not supported", data_format)
        return
    _module_logger.debug("%s", json.dumps(values_dict, indent=4))
    try:
        values_yml = values_dict["data"]["data"]["values.yml"]
    except KeyError:
        _module_logger.error("No values found")
        return 1
    _module_logger.debug(values_yml)
    with open(values_file, "w") as foo:
        foo.write(values_yml)
    return 0


def read_secret(secret_path: str, mval: str, data_format: str) -> int:
    """
    Read secret.

    :param secret_path: where to write secrets
    :param mval: value to read
    :param data_format: format, i.e. yaml or json
    :returns: error code
    """
    _module_logger.debug("Secret path %s: %s", secret_path, mval)
    data_file = os.path.join(secret_path, f"{mval}.{data_format}")
    data_path = os.path.dirname(data_file)
    _module_logger.debug("Create path %s", data_path)
    try:
        os.makedirs(data_path)
    except FileExistsError:
        pass
    _module_logger.info("Get secret %s (write %s)", mval, data_file)
    try:
        kv_out = subprocess.run(
            ["vault", "kv", "get", "-format", data_format, mval],
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        _module_logger.error("Could not get secret %s", mval)
        # Create empty file
        with open(data_file, "w") as foo:
            os.utime(data_file, None)
        return 1
    secret_data = kv_out.stdout
    _module_logger.debug("%s", secret_data)
    with open(data_file, "w") as foo:
        foo.write(secret_data)
    read_secret_values(secret_path, mval, secret_data, data_format)
    return 0


def read_secrets(
    secret_path: str,
    mid_aiv_paths: list,
    mid_aiv_secrets: list,
    vault_paths: list,
    data_format: str,
) -> int:
    """
    Read secrets.

    :param secret_path: where to write secrets
    :param mid_aiv_paths: Vault paths
    :param mid_aiv_secrets: initial list of secrets
    :param vault_paths: initial list of paths
    :param data_format: format, i.e. yaml or json
    :returns: error code
    """
    _module_logger.debug("Secrets path %s", secret_path)

    for vault_path in vault_paths:
        if vault_path[-1:] != "/":
            vault_path += "/"
        kvs = kv_list(vault_path)
        for kv in kvs:
            if not kv:
                pass
            elif kv[-1:] == "/":
                if kv not in mid_aiv_paths:
                    _module_logger.debug("Add path %s", kv)
                    mid_aiv_paths.append(f"{vault_path}{kv}")
            else:
                if kv not in mid_aiv_secrets:
                    mid_aiv_secrets.append(f"{vault_path}{kv}")

    while True:
        added = 0
        for mpath in mid_aiv_paths:
            kvs = kv_list(mpath)
            for kv in kvs:
                if not kv:
                    pass
                elif kv[-1:] == "/":
                    new_path = f"{mpath}{kv}"
                    if new_path not in mid_aiv_paths:
                        _module_logger.debug("New path %s", new_path)
                        mid_aiv_paths.append(new_path)
                        added += 1
                else:
                    new_secret = f"{mpath}{kv}"
                    if new_secret not in mid_aiv_secrets:
                        _module_logger.debug("New secret %s", new_secret)
                        mid_aiv_secrets.append(new_secret)
                        added += 1
        if not added:
            break

    # print("Paths:")
    # for mpath in sorted(mid_aiv_paths):
    #     print(f"\t{mpath}")
    # print()
    for mval in sorted(mid_aiv_secrets):
        read_secret(secret_path, mval, data_format)

    return 0


def kv_list(vault_path: str) -> list:
    """
    Read path.

    :param vault_path: vault path
    :returns: list of paths found
    """
    _module_logger.debug("List path %s", vault_path)
    try:
        kv_out = subprocess.run(["vault", "kv", "list", vault_path], stdout=subprocess.PIPE, text=True, check=True)
    except subprocess.CalledProcessError:
        _module_logger.error("Could not list path %s", vault_path)
        return []
    kvs = kv_out.stdout.split("\n")[2:]
    _module_logger.info("Path %s: %s", vault_path, ",".join(kvs))
    return kvs


def usage(p_name: str) -> None:
    print("Usage")
    print(f"\t {p_name} [--host=<VAULT_HOST>] [--path=<VAULT_PATH>]")
    return


def main(y_arg: list) -> int:
    """
    Start here.

    :param y_arg: list of arguments
    :returns: error code
    """
    mid_aiv_paths = []
    mid_aiv_secrets = []
    vault_host ="https://vault.skao.int/"
    vault_path = ""
    vault_paths = []
    vault_token = ""
    data_format = ""

    try:
        opts, _args = getopt.getopt(
            y_arg[1:],
            "hvVF:H:P:T:",
            [
                "help",
                "format=",
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
        elif opt in ("-F", "--format"):
            data_format = arg.lower()
            if data_format not in DATA_FORMATS:
                 _module_logger.error("Invalid format %s", data_format)
                 return 1
        elif opt in ("-H", "--host"):
            vault_host = arg
        elif opt in ("-P", "--path"):
            if "," in arg:
                vault_paths = arg.split(",")
            else:
                vault_paths = [arg]
        elif opt in ("-T", "--token"):
            vault_token = arg
        elif opt == "-v":
            _module_logger.setLevel(logging.INFO)
            _module_logger.warning("Set level to info")
        elif opt == "-V":
            _module_logger.setLevel(logging.DEBUG)
            _module_logger.warning("Set level to debug")
        else:
            _module_logger.error("Invalid option %s", opt)

    _module_logger.info("Start client for %s", vault_host)
    client = hvac.Client(url=vault_host)

    if not client.is_authenticated():
        _module_logger.error(f"Client for host {vault_host} is not authenticated")
        return 1

    if not vault_paths:
        vault_paths = MID_AIV_MOUNTS
    if not data_format:
        data_format = DEFAULT_DATA_FORMAT

    read_secrets(DATA_PATH, mid_aiv_paths, mid_aiv_secrets, vault_paths, data_format)

    return 0


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
