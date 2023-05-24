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
V ?= -v
GAIA_IP ?= 10.165.3.7
PI_IP ?= 10.165.3.11
SUDO_USER ?= $(USER)
SSH_USER ?= $(USER)

vars:  ## Variables
	@echo "Current variable settings:"
	@echo "INVENTORY_FILE=$(INVENTORY_FILE)"
	@echo "PLAYBOOK_PARAMETERS=$(PLAYBOOK_PARAMETERS)"
	@echo "NODES=$(NODES)"
	@echo "SUDO_USER=$(SUDO_USER)"
	@echo "SSH_USER=$(SSH_USER)"
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

setup_pi:
	ansible-playbook -i $(INVENTORY_FILE) --limit raspberry_pi \
	  main.yml \
	  $(PLAYBOOK_PARAMETERS) \
	  -u=$(SUDO_USER) \
	  $(V)
.PHONY: setup_pi

setup_pi_dry_run:
	ansible-playbook -i $(INVENTORY_FILE) --limit raspberry_pi \
	  main.yml \
	  $(PLAYBOOK_PARAMETERS) \
	  -u=$(SUDO_USER) \
	  --check \
	  --diff \
	  $(V)
.PHONY: setup_pi_dry_run

setup_gaia:
	ansible-playbook -i $(INVENTORY_FILE) --limit gaia \
	  main.yml \
	  $(PLAYBOOK_PARAMETERS) \
	  -u=$(SUDO_USER) \
	  $(V)
.PHONY: setup_gaia

setup_gaia_dry_run:
	ansible-playbook -i $(INVENTORY_FILE) --limit gaia \
	  main.yml \
	  $(PLAYBOOK_PARAMETERS) \
	  -u=$(SUDO_USER) \
	  --check \
	  --diff \
	  $(V)
.PHONY: setup_gaia

lint: ## Lint check playbook
	ansible-lint -vvv main.yml
.PHONY: lint

test: test-default test-gaia test-raspberry_pi
.PHONY: test

test-default:
	testing/run.sh ansible-test-default default
.PHONY: test-default

test-gaia:
	testing/run.sh ansible-test-gaia gaia
.PHONY: test-gaia

test-raspberry_pi:
	testing/run.sh ansible-test-default raspberry_pi
.PHONY: test-raspberry_pi

test-cicd: test-cicd-default test-cicd-gaia test-cicd-raspberry_pi
.PHONY: test-cicd

test-cicd-default: CONTAINER_HOST := ansible-test-default
test-cicd-default:
	testing/test.sh ${CONTAINER_HOST} default
.PHONY: test-cicd-default

test-cicd-gaia: CONTAINER_HOST := ansible-test-gaia
test-cicd-gaia:
	testing/test.sh ${CONTAINER_HOST} gaia
.PHONY: test-cicd-gaia

test-cicd-raspberry_pi: CONTAINER_HOST := ansible-test-raspberry-pi
test-cicd-raspberry_pi:
	testing/test.sh ${CONTAINER_HOST} raspberry_pi
.PHONY: test-cicd-raspberry_pi

help:  ## show this help.
	@echo "make targets:"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ": .*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo ""; echo "make vars (+defaults):"
	@grep -E '^[0-9a-zA-Z_-]+ \?=.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = " \\?= "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

echo_vars:
	@echo "Variables:"
	@echo $(PRIVATE_VARS)
.PHONY: echo_vars

list_tasks:
	ansible-playbook -i $(INVENTORY_FILE) \
		main.yml \
		$(PLAYBOOK_PARAMETERS) \
		--list-tasks
.PHONY: list_tasks

