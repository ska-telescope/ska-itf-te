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

This sub-project contains Ansible playbooks used to manage server configuration in the MID ITF.

In order for this tooling to work for you, you must already have `ssh` access to the inventory described in `inventory/hosts`.

## Project Layout

### group_vars

This directory contains the variables applicable to all roles.

### inventory

This directory contains the hosts inventory on which playbooks are executed.

### roles

#### ssh

### distribute_ssh_keys.yml

This is the Ansible playbook and contains all the tasks we execute in order to add/remove keys and create/delete users. Tasks are executed based on tags and tasks which match the current tag are executed in order.

### inventory_ssh_keys

This contains the hosts for which we execute our Ansible playbook. They are grouped according to their function and the group names can be used to specify which hosts to execute the playbook for.

### Makefile

The `Makefile` contains targets to add/remove keys and create/delete users.

### ssh_key_vars.yml

This contains pre-populated variables used in the execution of the playbook. In particular, `all_ssh_keys` contains the list of SSH public keys which we can push to hosts and `user_groups_by_host_group` specify which user groups are used on which host groups. The SSH keys have been directly copied from the `resources/users/*/.ssh` folders.

## Environment Setup

### Local (Private) Variables

Populate your `PrivateRules.mak` file with something like

```bash
EXTRA_VARS="mode=test" # This helps skipping some desctructive steps on the BIFROST

# Usage parameters
SSH_USER=<your-first-name>
```

## Add a key

To add a configured key in `all_ssh_keys`, run:

```sh
# $USER is the user who's key you want to add
# $HOST_GROUP is the host group you want to run the command for.
make addkey PLAYBOOK_PARAMETERS="-u=$USER -k" NODES=$HOST_GROUP
```

Example:

```sh
# Add a key for the user 'jan.kowalski' on all gaia hosts.
make addkey PLAYBOOK_PARAMETERS="-u=jan.kowalski -k" NODES=gaia
```

NOTE: the user account needs to exist already. If you cannot use `make adduser`, speak to IT about this.

## Remove a key

To remove the user's configured key in `all_ssh_keys`, run:

```sh
# $USER is the user who's key you want to remove
# $HOST_GROUP is the host group you want to run the command for.
make removekey PLAYBOOK_PARAMETERS="-u=$USER" NODES=$HOST_GROUP
```

Example:

```sh
# Remove the user 'erika.mustermann''s key from all gaia hosts.
make removekey PLAYBOOK_PARAMETERS="-u=erika.mustermann" NODES=gaia
```

## Add a user

In order to create a user and add it's key on a host, you will need `sudo` rights on the host.
You can run the following command to create the user and add their key:

```sh
# $SUDO_USER is the user with sudo rights.
# $NEW_USER is the user you want to create.
# $HOST_GROUP is the host group you want to run the command for.
make adduser PLAYBOOK_PARAMETERS="-u=$SUDO_USER -kK --extra-vars user_name=$NEW_USER" NODES=$HOST_GROUP
```

Example:

```sh
# Creates a new user 'erika.mustermann' on all gaia hosts and pushes her SSH public key there as well. The user 'minta.kata' already exists on the hosts and has sudo rights.
make adduser PLAYBOOK_PARAMETERS="-u=minta.kata -kK --extra-vars user_name=erika.mustermann" NODES=gaia
```

## Remove a user

In order to remove a user from a host, you will need `sudo` rights on the host.
You can run the following command to remove the user (note this will remove their home directory as well):

```sh
# $SUDO_USER is the user with sudo rights.
# $REMOVE_USER is the user you want to remove.
# $HOST_GROUP is the host group you want to run the command for.
make removeuser PLAYBOOK_PARAMETERS="-u=$SUDO_USER -kK --extra-vars user_name=$REMOVE_USER" NODES=$HOST_GROUP
```

Example:

```sh
# Removes the user 'marte.kirkerud' on all gaia hosts. The user 'kari.holm' exists on the hosts and has sudo rights.
make removeuser PLAYBOOK_PARAMETERS="-u=kari.holm -kK --extra-vars user_name=marte.kirkerud" NODES=gaia
```

## Limiting Scope

We use the `NODES` parameter to limit which hosts the command will run on. This can be set to any inventory group (see `inventory_ssh_keys`). It is possible, but not recommended to run the commands without this filter.

## Local Testing

The `NODES` parameter can also be used to test the commands locally.
You can achieve this by setting `NODES` to the `home` group:

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
