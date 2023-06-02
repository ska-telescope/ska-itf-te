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

This directory contains the variables applicable to all roles. The `all.yml` file contains default values for these variables. The directories in this folder contain team-specific configuration.

### inventory

This directory contains the hosts inventory on which playbooks are executed.

### roles

#### kubectl_setup

This role configures the host for access to a kubernetes cluster.
Currently it does the following:

1. Sets the KUBECONFIG environment variable to the kubeconfig stored in the team's shared config directory.
1. Adds kubectl aliases and autocompletion.

#### ssh_keys

This role adds a user's SSH public key to their `authorized_keys` on the host. The keys are defined in `resources/users`.

#### system_setup

This role contains tasks related to system-level configuration. Some of the tasks which can be defined here are:

1. Installation of packages
2. Creation of groups
3. Creation of files & directories

#### status

This role is used to setup a status page for services running in the ITF.
It runs on Gaia.

#### user_config

This role is used to add additional configuration for users. Currently it provides the following functionality:

1. Adds an ssh config file which provides easy SSH access to other nodes in the ITF.
2. Adds useful bash aliases.
3. Adds a welcome message, displayed at login.

#### user_setup

This role is used to create & remove users, and also to add existing users to groups.

#### var_setup

This role parses the team configuration into variables which are easier to use by the various other roles.

### testing

This directory contains scripts used to test the execution of the playbooks on containers.

### site.yml

This is the Ansible playbook and contains all the tasks we execute in order to add/remove keys and create/delete users. Tasks are executed based on tags and tasks which match the current tag are executed in order.

## Environment Setup

### Local (Private) Variables

Populate your `PrivateRules.mak` file with something like

```bash
# Set this to the team for which you want to execute the plays.
# There must be a directory matching this name in group_vars.
TEAM=<your-team>
# This is the user used to SSH to hosts in the connect_* targets.
SSH_USER=<your-jira-username>
# This is the user used to execute Ansible playbooks.
ANSIBLE_USER=<your-jira-username>
# This allows you to filter the playbook to only execute for specific users (e.g. yourself).
PLAYBOOK_PARAMETERS=--extra-vars='{"users": [<your-jira-username>]}'
# Enable verbose logging in Ansible
V=-v
```

## Execute a play

We currently have 3 plays defined in our playbook: one each for Gaia & Raspberry Pi, and a test play which runs with all features enabled. Each play executes most of the following actions:

1. Install any dependencies missing from the host (e.g. kubectl).
2. Create any team groups if they do not exist.
3. Create a shared directory `/srv` if it does not exist.
4. Create a common shared directory `/srv/all` if it does not exist. This is writable by all.
5. Create team shared directories at `/srv/<team>` if they do not exist. These are only readable/writable by the team members.
6. Create any required subdirectories in the team shared directories.
7. Create users if the do not exist (not executed on gaia).
8. Add users to the team and sudo groups.
9. Add configured SSH public keys to `authorized_keys` for users.
10. Add SSH config for the users which enables them easily SSH to other nodes in the ITF.
11. Add useful bash aliases for the users.
12. Add a welcome script which prints a message for the users at login.
13. Add a script which sets the KUBECONFIG environment variable to a default kubeconfig in the team's configuration directory.

### Gaia

The Gaia play can be executed as follows:

```bash
make setup_gaia
```

### Raspberry Pi

The Raspberry Pi play can be executed as follows:

```bash
make setup_raspberry_pi
```

## Testing

Tests can be executed as follows:

```bash
# run all the playbook tests
make test
# run a single playbook test (the one for gaia)
make test_gaia
```

## Additional Info

### Help

Run `make` to get the help:

```sh
$ make
make targets:
help                           show this help.
lint                           Lint check playbook
remove                         Remove keys
vars                           Variables

make vars (+defaults):
INVENTORY_FILE                 ./inventory_ssh_keys
NODES                          nodes ## subset of hosts from inventory to run against
PRIVATE_VARS                   ./ssh_key_vars.yml
```

### Dry run

You can execute `setup_pi_dry_run` or `setup_gaia_dry_run` to run the playbooks in dry-run mode. This will result in Ansible predicting what changes will occur if the playbook were to be run and output these as a diff.

### Connect

You can connect to the ITF with `make connect_pi` or `make connect_gaia`. This SSH's to the host with agent forwarding enabled.

### CI/CD

The ansible jobs are defined in the top-level CI/CD file. This is because there was an issue with detecting some of the jobs when they were defined in this directory. Each job extends the `setup-ansible` job to install dependencies and set the locale.

#### ansible-lint

This job just executes the `ansible-lint` command on our playbook. It should be replaced with the `ansible-lint` job from the Ansible Gitlab template.

### ansible-test

This job runs the container test executions of the plays. It does this by starting up containers for each test using Gitlab services and then running `make test-cicd`.
