# distribute-ssh-keys

Update SSH keys on the Atlas team's hosts.

## Prerequisites

### ansible

To install and use the package, make sure you have no virtual environment active. Change Directory into this one (same as this `README`), run `poetry shell` and then `poetry install` - this should install Ansible in a new virtual environment.

### ansible-lint

`ansible-lint` is used to lint our Ansible playbooks. See [this page](https://ansible-lint.readthedocs.io) for more details. It can be installed as follows:

```sh
python -m pip install --user ansible-lint
# or
pip3 install ansible-lint
```

## Summary

This tool adds and removes ssh keys across the MID ITF.

Update `ssh_key_vars.yml` as the input for `add_ssh_keys` and `remove_ssh_keys`.

In order for this tool to work for you, you must already have `ssh` access to the inventory described in `inventory_ssh_keys`.

## Add keys to all inventory

To add the configured keys in `add_ssh_keys` to all hosts, run:

```sh
make add
```

## Remove keys from all inventory

To remove the configured keys in `remove_ssh_keys` from hosts, run:

```sh
make remove
```

## Limiting

To limit the scope of inventory updated, set `NODES` to the appropriate inventory group, eg:

```sh
make add NODES=gaia
```

This would add the list of keys to nodes in the `gaia` group as described by the `inventory_ssh_keys` file.
This can be used to test locally:

```sh
make add NODES=home
```

This command adds the keys to your local `~/.ssh/authorized_keys`

## Additonal Info

Run `make` to get the help:

```sh
$ make
make targets:
add                            Add keys
help                           show this help.
lint                           Lint check playbook
remove                         Remove keys
vars                           Variables

make vars (+defaults):
INVENTORY_FILE                 ./inventory_ssh_keys
NODES                          nodes ## subset of hosts from inventory to run against
PRIVATE_VARS                   ./ssh_key_vars.yml
```
