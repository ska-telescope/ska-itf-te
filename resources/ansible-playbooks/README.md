# ansible-playbooks

Manage server configuration and user access in the Mid ITF.

## Setup

To install and use the playbooks, make sure you have no virtual environment active. Change Directory into this one (same as this `README`), run `poetry shell` and then `poetry install` - this should install Ansible in a new virtual environment. You can find more details on managing environments with poetry [here](https://python-poetry.org/docs/managing-environments/).

## Summary

This sub-project contains Ansible playbooks used to manage user access and server configuration in the MID ITF.

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

#### local_ssh

This role adds an SSH config file at `~/.ssh/config.d/ska-mid-itf-config` which is also included in your main SSH config file. This file sets up SSH access to hosts in the Mid ITF. It adds access to the following hosts:

* Gaia (10.165.4.7): `ssh gaia`
* Raspberry Pi 0 (10.165.4.11): `ssh pi0`
* Raspberry Pi 4 (10.165.4.15): `ssh pi4`
* Talon Board 1 (10.165.4.29): `ssh talon1`
* Talon Board 2 (10.165.4.30): `ssh talon2`

#### ssh_keys

This role adds a user's SSH public key to their `authorized_keys` on the host. The keys are defined in `resources/users/<team>/<user>/.ssh`.

#### system_setup

This role contains tasks related to system-level configuration. Some of the tasks which can be defined here are:

1. Installation of packages
2. Creation of groups
3. Creation of files & directories

#### team_setup

This role contains tasks related to the configuration of the host for a specific team. For example, creating team groups and shared directories.

#### update_talon

This role is used to update the Talon boards. At the moment it just sets the DNS IP address in their network configuration.

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

Populate your `PrivateRules.mak` file with something like:

```bash
# Set this to the team for which you want to execute the plays.
# There must be a directory matching this name in group_vars.
TEAM=<your-team>
# This allows you to filter the playbook to only execute for specific users (e.g. yourself).
PLAYBOOK_PARAMETERS=--extra-vars='{"users": [<your-jira-username>]}'
# Enable verbose logging in Ansible
V=-v
# Jira username - used to setup local environment
AD_USER=<your-active-directory-username>
```

The `AD_USER` environment variable is required for all of the playbooks. The `TEAM` environment variable is required for the Gaia & Raspberry Pi playbooks.

## Execute a play

We currently have 5 plays defined in our playbook:

1. Setup gaia
2. Setup rasperry_pi
3. Setup test
4. Setup Talon Dx boards
5. Install Mid ITF SSH config on localhost

*Setup gaia* and *Setup rasperry_pi* each execute most of the following actions:

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

*Setup test* is used to test the functionality against a Docker container and exercises all the functionality in 'Setup gaia' and 'Setup raspberry_pi'.

*Setup Talon Dx boards* is currently just used to configure DNS on the Talon Dx boards.

*Install Mid ITF SSH config on localhost* sets up your local machine to easily SSH onto hosts in the Mid ITF.

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

### Talon Dx Boards

The Talon Dx Board play can be executed as follows:

```bash
make setup_talon_boards
```

### Local SSH config

The local SSH config play can be executed as follows:

```bash
make setup_local_ssh_config
```

## Running Tests

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
Makefile:help                  Show this help.
Makefile:lint                  Lint check playbook
Makefile:list_tasks            Prints the tasks to be executed during a playbook run.
Makefile:setup_gaia_dry_run    Runs the full playbook against Gaia in dry-run mode.
Makefile:setup_gaia            Runs the full playbook against Gaia.
Makefile:setup_local_ssh_config_dry_run Sets up your localhost for using the ansible playbooks (dry-run mode).
Makefile:setup_local_ssh_config Sets up your localhost for using the ansible playbooks.
Makefile:setup_pi_dry_run      Runs the full playbook against the Raspberry Pi in dry-run mode.
Makefile:setup_pi              Runs the full playbook against the Raspberry Pi.
Makefile:setup_talon_boards_dry_run Runs the full playbook against the Talon boards in dry-run mode.
Makefile:setup_talon_boards    Runs the full playbook against the Talon boards.
Makefile:test-cicd-default     Runs a playbook test with all flags enabled (intended for Gitlab pipelines).
Makefile:test-cicd-gaia        Runs a playbook test as if it were against Gaia (intended for Gitlab pipelines).
Makefile:test-cicd-raspberry_pi Runs a playbook test as if it were against the Raspberry Pi (intended for Gitlab pipelines).
Makefile:test-cicd             Runs all playbook tests (intended for Gitlab pipelines).
Makefile:test-default          Runs a playbook test with all flags enabled.
Makefile:test-gaia             Runs a playbook test as if it were against Gaia.
Makefile:test-raspberry_pi     Runs a playbook test as if it were against the Raspberry Pi.
Makefile:test                  Runs all playbook tests.
Makefile:vars                  Variables
```

Run `make vars` to get your current environment variables:

```bash
Current variable settings:
INVENTORY_TEMPLATE=inventory/hosts-template
INVENTORY_FILE=inventory/hosts
PLAYBOOK_PARAMETERS=--extra-vars='{filter_users: [p.jordaan]}'
TEAM=atlas
TEAM_VARS_FILE=./group_vars/atlas/atlas.yml
AD_USER=p.jordaan
ANSIBLE_COMMAND=ansible-playbook -i inventory/hosts -e @./group_vars/atlas/atlas.yml --extra-vars='{filter_users: [p.jordaan]}' -vvv
ANSIBLE_COMMAND_DRY_RUN=ansible-playbook -i inventory/hosts -e @./group_vars/atlas/atlas.yml --extra-vars='{filter_users: [p.jordaan]}' -vvv --check --diff
V=-vvv
```

### Dry run

You can execute each of the plays with a `_dry_run` suffix to run the playbooks in dry-run mode. This will result in Ansible predicting what changes will occur if the playbook were to be run and output these as a diff.

For example:

```bash
make setup_gaia_dry_run
```

Note that some of the plays can fail in dry run mode due to resources or variables not existing.

### CI/CD

The ansible jobs are defined in the CI/CD file at `.gitlab/ci/ansible.yml` from the project root directory. Each job extends the `setup-ansible` job to install dependencies and set the locale.

#### ansible-lint

This job just executes the `ansible-lint` command on our playbook. It should be replaced with the `ansible-lint` job from the Ansible Gitlab template.

### ansible-test

This job runs the container test executions of the plays. It does this by starting up containers for each test using Gitlab services and then running `make test-cicd`.
