.DEFAULT_GOAL := help

# include makefile targets from the submodule
include ../../.make/oci.mk

# include core make support
include ../../.make/base.mk

# include core make support
include ../../.make/release.mk

# define overides for above variables in here
-include PrivateRules.mak

INVENTORY_FILE ?= ./inventory/hosts
PLAYBOOK_PARAMETERS ?= ## any additional ansible tags can go here - see ansible-playbook --help
NODES ?= nodes ## subset of hosts from inventory to run against
SSH_USER ?= $(USER)
TEAM ?= atlas
TEAM_VARS_FILE ?= ./group_vars/$(TEAM)/$(TEAM).yml
ANSIBLE_COMMAND := ansible-playbook -i $(INVENTORY_FILE) -e @$(TEAM_VARS_FILE) $(PLAYBOOK_PARAMETERS) $(V)
ifneq ($(ANSIBLE_USER),)
ANSIBLE_COMMAND := $(ANSIBLE_COMMAND) -u=$(ANSIBLE_USER)
endif
ANSIBLE_COMMAND_DRY_RUN := $(ANSIBLE_COMMAND) --check --diff
GAIA_IP ?= 10.165.3.7
PI_IP ?= 10.165.3.11
V ?=

vars:  ## Variables
	@echo "Current variable settings:"
	@echo "INVENTORY_FILE=$(INVENTORY_FILE)"
	@echo "PLAYBOOK_PARAMETERS=$(PLAYBOOK_PARAMETERS)"
	@echo "NODES=$(NODES)"
	@echo "ANSIBLE_USER=$(ANSIBLE_USER)"
	@echo "SSH_USER=$(SSH_USER)"
	@echo "TEAM=$(TEAM)"
	@echo "TEAM_VARS_FILE=$(TEAM_VARS_FILE)"
	@echo "ANSIBLE_COMMAND=$(ANSIBLE_COMMAND)"
	@echo "ANSIBLE_COMMAND_DRY_RUN=$(ANSIBLE_COMMAND_DRY_RUN)"
	@echo "GAIA_IP=$(GAIA_IP)"
	@echo "PI_IP=$(PI_IP)"
	@echo "V=$(V)"
.PHONY: vars

connect_gaia: ## Add SSH Forwarding to local machine and SSH into Gaia
	@echo "Connecting to the Gaia as $(SSH_USER)";
	@echo "###########################################";
	ssh -A $(SSH_USER)@$(GAIA_IP);
	@echo "Welcome back";
.PHONY: connect_gaia

connect_pi: ## Add SSH Forwarding to local machine and SSH into Gaia
	@echo "Connecting to the Raspberry Pi as $(SSH_USER)";
	@echo "###########################################";
	ssh -A $(SSH_USER)@$(PI_IP);
	@echo "Welcome back";
.PHONY: connect_pi

setup_pi: ## Runs the full playbook against the Raspberry Pi.
	$(ANSIBLE_COMMAND) --limit raspberry_pi site.yml
.PHONY: setup_pi

setup_pi_dry_run: ## Runs the full playbook against the Raspberry Pi in dry-run mode.
	$(ANSIBLE_COMMAND_DRY_RUN) --limit raspberry_pi site.yml
.PHONY: setup_pi_dry_run

setup_gaia: ## Runs the full playbook against Gaia.
	$(ANSIBLE_COMMAND) --limit gaia site.yml
.PHONY: setup_gaia

setup_gaia_dry_run: ## Runs the full playbook against Gaia in dry-run mode.
	$(ANSIBLE_COMMAND_DRY_RUN) --limit gaia site.yml
.PHONY: setup_gaia

setup_talon_boards: ## Runs the full playbook against the Talon boards.
	$(ANSIBLE_COMMAND) --limit talon site.yml
.PHONY: setup_talon

setup_talon_boards_dry_run: ## Runs the full playbook against the Talon boards in dry-run mode.
	$(ANSIBLE_COMMAND_DRY_RUN) --limit talon site.yml
.PHONY: setup_talon_boards_dry_run

setup_localhost: ## Sets up your localhost for using the ansible playbooks.
	$(ANSIBLE_COMMAND) --limit localhost site.yml --extra-vars='{"jira_user": "$(JIRA_USER)"}'
.PHONY: setup_localhost

setup_localhost_dry_run: ## Sets up your localhost for using the ansible playbooks (dry-run mode).
	$(ANSIBLE_COMMAND_DRY_RUN) --limit localhost site.yml --extra-vars='{"jira_user": "$(JIRA_USER)"}'
.PHONY: setup_localhost_dry_run

lint: ## Lint check playbook
	ansible-lint -vvv site.yml
.PHONY: lint

test: test-default test-gaia test-raspberry_pi ## Runs all playbook tests.
.PHONY: test

test-default: ## Runs a playbook test with all flags enabled.
	testing/run.sh ansible-test-default default
.PHONY: test-default

test-gaia: ## Runs a playbook test as if it were against Gaia.
	testing/run.sh ansible-test-gaia gaia
.PHONY: test-gaia

test-raspberry_pi: ## Runs a playbook test as if it were against the Raspberry Pi.
	testing/run.sh ansible-test-default raspberry_pi
.PHONY: test-raspberry_pi

test-cicd: test-cicd-default test-cicd-gaia test-cicd-raspberry_pi ## Runs all playbook tests (intended for Gitlab pipelines).
.PHONY: test-cicd

# TEST_HOST is the name of the service started up in the pipeline.
# See the ansible-test job in the .gitlab-ci.yml.
test-cicd-default: TEST_HOST := ansible-test-default ## Runs a playbook test with all flags enabled (intended for Gitlab pipelines).
test-cicd-default:
	testing/test.sh default
.PHONY: test-cicd-default

test-cicd-gaia: TEST_HOST := ansible-test-gaia ## Runs a playbook test as if it were against Gaia (intended for Gitlab pipelines).
test-cicd-gaia:
	testing/test.sh gaia
.PHONY: test-cicd-gaia

test-cicd-raspberry_pi: TEST_HOST := ansible-test-raspberry-pi ## Runs a playbook test as if it were against the Raspberry Pi (intended for Gitlab pipelines).
test-cicd-raspberry_pi:
	testing/test.sh raspberry_pi
.PHONY: test-cicd-raspberry_pi

# Note: in order for a target to show up in the help message,
# it needs to have a comment starting with '##' on the same line.
help:  ## Show this help.
	@echo "make targets:"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ": .*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo ""; echo "make vars (+defaults):"
	@grep -E '^[0-9a-zA-Z_-]+ \?=.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = " \\?= "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

echo_vars:
	@echo "Variables:"
	@echo $(PRIVATE_VARS)
.PHONY: echo_vars
