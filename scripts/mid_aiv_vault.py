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
DEFAULT_SECRET_ENGINES = ["cubbyhole/", "dev/", "mid-aa/", "mid-itf/", "shared/"]
DEFAULT_DATA_PATH = "tmp/vault"
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
    secret_data_path: str,
    mval: str,
    secret_data: str,
    data_format: str,
    create_empty: bool,
) -> int:
    """
    Read secret values.

    :param secret_data_path: where to write secrets
    :param data_format: format, i.e. yaml or json
    :param create_empty: create empty directories and files
    :returns: error code
    """
    _module_logger.debug("Secret values path %s: %s", secret_data_path, mval)
    values_path = os.path.join(secret_data_path, mval)
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
        return 1
    _module_logger.debug("%s", json.dumps(values_dict, indent=4))
    try:
        values_yml = values_dict["data"]["data"]["values.yml"]
    except TypeError:
        values_yml = ""
    except KeyError:
        values_yml = ""
    if not values_yml:
        _module_logger.warning("No values found")
        if create_empty:
            with open(values_file, "w") as foo:
                os.utime(values_file, None)
            return 0
        return 1
    _module_logger.debug(values_yml)
    with open(values_file, "w") as foo:
        foo.write(values_yml)
    return 0


def read_secret(
    secret_data_path: str, mval: str, data_format: str, create_empty: bool
) -> int:
    """
    Read secret.

    :param secret_data_path: where to write secrets
    :param mval: value to read
    :param data_format: format, i.e. yaml or json
    :param create_empty: create empty directories and files
    :returns: error code
    """
    _module_logger.debug("Secret path %s: %s", secret_data_path, mval)
    data_file = os.path.join(secret_data_path, f"{mval}.{data_format}")
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
        if create_empty:
            # Create empty file
            with open(data_file, "w") as foo:
                os.utime(data_file, None)
            return 0
        return 1
    secret_data = kv_out.stdout
    _module_logger.debug("%s", secret_data)
    with open(data_file, "w") as foo:
        foo.write(secret_data)
    read_secret_values(secret_data_path, mval, secret_data, data_format, create_empty)
    return 0


def read_secret_engines(
    secret_data_path: str,
    secret_engines: list,
    data_format: str,
    create_empty: bool,
) -> int:
    """
    Read secret engines.

    :param secret_data_path: where to write secrets
    :param secret_engines: initial list of paths
    :param data_format: format, i.e. yaml or json
    :param create_empty: create empty directories and files
    :returns: error code
    """
    mid_aiv_paths: list = []
    mid_aiv_secrets: list = []
    _module_logger.debug("Secrets path %s", secret_data_path)

    for secret_engine in secret_engines:
        if secret_engine[-1:] != "/":
            secret_engine += "/"
        kvs = kv_list(secret_data_path, secret_engine, create_empty)
        for kv in kvs:
            if not kv:
                if create_empty:
                    emptydir = os.path.join(secret_data_path, secret_engine)
                    try:
                        os.makedirs(emptydir)
                    except FileExistsError:
                        pass
            elif kv[-1:] == "/":
                if kv not in mid_aiv_paths:
                    _module_logger.debug("Add path %s", kv)
                    mid_aiv_paths.append(f"{secret_engine}{kv}")
            else:
                if kv not in mid_aiv_secrets:
                    mid_aiv_secrets.append(f"{secret_engine}{kv}")

    while True:
        added = 0
        for mpath in mid_aiv_paths:
            kvs = kv_list(secret_data_path, mpath, create_empty)
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
        read_secret(secret_data_path, mval, data_format, create_empty)

    return 0


def kv_list(secret_data_path: str, vault_path: str, create_empty: bool) -> list:
    """
    Read path.

    :param secret_data_path: where to write secrets
    :param vault_path: vault path
    :param create_empty: create empty directories and files
    :returns: list of paths found
    """
    _module_logger.debug("List path %s", vault_path)
    try:
        kv_out = subprocess.run(["vault", "kv", "list", vault_path], stdout=subprocess.PIPE, text=True, check=True)
    except subprocess.CalledProcessError:
        _module_logger.warning("Could not list path %s", vault_path)
        if create_empty:
            emptydir = os.path.join(secret_data_path, vault_path)
            try:
                os.makedirs(emptydir)
            except FileExistsError:
                pass
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
    secrets_data_path: str = ""
    vault_host: str = "https://vault.skao.int/"
    secret_engines: list = []
    vault_token: str = ""
    data_format: str = ""
    create_empty: bool = False

    # Read command line
    try:
        opts, _args = getopt.getopt(
            y_arg[1:],
            "ehvVD:E:F:H:P:T:",
            [
                "help",
                "empty",
                "data=",
                "engines=",
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

    # Read options
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(os.path.basename(y_arg[0]))
            sys.exit(1)
        elif opt in ("-D", "--data"):
            secrets_data_path = arg
        elif opt in ("-e", "--empty"):
            create_empty = True
        elif opt in ("-F", "--format"):
            data_format = arg.lower()
            if data_format not in DATA_FORMATS:
                 _module_logger.error("Invalid format %s", data_format)
                 return 1
        elif opt in ("-H", "--host"):
            vault_host = arg
        elif opt in ("-P", "--path"):
            if "," in arg:
                secret_engines = arg.split(",")
            else:
                secret_engines = [arg]
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

    # Set up vault client
    _module_logger.info("Start client for %s", vault_host)
    client = hvac.Client(url=vault_host)
    if not client.is_authenticated():
        _module_logger.error(f"Client for host {vault_host} is not authenticated")
        return 1

    # Check values and use defaults as needed
    if not secrets_data_path:
        secrets_data_path = DEFAULT_DATA_PATH
    try:
        os.makedirs(secrets_data_path)
    except FileExistsError:
        pass
    if not secret_engines:
        secret_engines = DEFAULT_SECRET_ENGINES
    if not data_format:
        data_format = DEFAULT_DATA_FORMAT

    read_secret_engines(secrets_data_path, secret_engines, data_format, create_empty)

    # client.delete()

    return 0


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
