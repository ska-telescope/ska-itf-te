INVENTORY_FILE ?= ./vars/inventory
PLAYBOOK_PARAMETERS ?= ## any additional ansible tags can go here - see ansible-playbook --help
NODES ?= nodes ## subset of hosts from inventory to run against
V ?=
GAIA_IP ?= 10.165.3.7
PI_IP ?= 10.165.3.11

.DEFAULT_GOAL := help

# include makefile targets from the submodule
include ../../.make/oci.mk

# include core make support
include ../../.make/base.mk

# include core make support
include ../../.make/release.mk

# define overides for above variables in here
-include PrivateRules.mak

vars:  ## Variables
	@echo "Current variable settings:"
	@echo "PRIVATE_VARS=$(PRIVATE_VARS)"
	@echo "INVENTORY_FILE=$(INVENTORY_FILE)"
	@echo "PLAYBOOK_PARAMETERS=$(PLAYBOOK_PARAMETERS)"
	@echo "NODES=$(NODES)"
	@echo "SSH_USER=$(SSH_USER)"
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
	  $(V)
.PHONY: setup_pi_dry_run

setup_gaia:
	ansible-playbook -i $(INVENTORY_FILE) --limit gaia \
	  main.yml \
	  $(PLAYBOOK_PARAMETERS) \
	  -u=$(SUDO_USER) \
	  $(V)
.PHONY: setup_gaia

lint: ## Lint check playbook
	ansible-lint -vvv main.yml
.PHONY: lint

test:
	testing/run.sh test
	testing/run.sh raspberry_pi
	testing/run.sh gaia
.PHONY: test

publish-test-images: publish-test-images-full publish-test-images-gaia
.PHONY: publish-test-images

publish-test-images-full: OCI_IMAGE := ska-mid-itf-ansible-test-full
publish-test-images-full: VERSION := 0.0.0
publish-test-images-full: oci-image-build
.PHONY: publish-test-images-full

publish-test-images-gaia: OCI_IMAGE := ska-mid-itf-ansible-test-gaia
publish-test-images-gaia: VERSION := 0.0.0
publish-test-images-gaia: oci-image-build
.PHONY: publish-test-images-gaia

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

