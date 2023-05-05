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

## Add a key to all inventory

To add a configured key in `add_ssh_keys` to all hosts, run:

```sh
# $USER is the user who's key you want to add
make addkey PLAYBOOK_PARAMETERS="-u=$USER"
```

NOTE: the user account needs to exist already. If you cannot use `make adduser`, speak to IT about this.

## Remove keys from all inventory

To remove the configured keys in `remove_ssh_keys` from hosts, run:

```sh
# $USER is the user who's key you want to remove
make removekeys PLAYBOOK_PARAMETERS="-u=$USER"
```

## Add a user

In order to create a user and add it's key on a host, you will need `sudo` rights on the host.
You can run the following command to create the user and add their key:
```sh
# $SUDO_USER is the user with sudo rights.
# $NEW_USER is the user you want to create.
make adduser PLAYBOOK_PARAMETERS="-u=$SUDO_USER -kK --extra-vars user_name=$NEW_USER"
```

## Remove a user

In order to remove a user from a host, you will need `sudo` rights on the host.
You can run the following command to remove the user (note this will remove their home directory as well):

```sh
# $SUDO_USER is the user with sudo rights.
# $REMOVE_USER is the user you want to remove.
make adduser PLAYBOOK_PARAMETERS="-u=$SUDO_USER -kK --extra-vars user_name=$REMOVE_USER"
```

## Limiting

To limit the scope of inventory updated, set `NODES` to the appropriate inventory group, eg:

```sh
make addkey PLAYBOOK_PARAMETERS="-u=$USER" NODES=gaia
```

This would add the list of keys to nodes in the `gaia` group as described by the `inventory_ssh_keys` file.
This can be used to test locally by using the `home` group:

```sh
make addkey PLAYBOOK_PARAMETERS="-u=$USER" NODES=home
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
