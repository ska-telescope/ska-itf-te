INVENTORY_FILE ?= ./inventory_ssh_keys
PRIVATE_VARS ?= ./ssh_key_vars.yml
PLAYBOOK_PARAMETERS ?= ## any additional ansible tags can go here - see ansible-playbook --help
NODES ?= nodes ## subset of hosts from inventory to run against
V ?=

.DEFAULT_GOAL := help

# define overides for above variables in here
-include PrivateRules.mak

vars:  ## Variables
	@echo "Current variable settings:"
	@echo "PRIVATE_VARS=$(PRIVATE_VARS)"
	@echo "INVENTORY_FILE=$(INVENTORY_FILE)"

all: add remove

lint: ## Lint check playbook
	ansible-lint distribute_ssh_keys.yml

addusers:  ## Create user accounts
	ansible-playbook -i $(INVENTORY_FILE) --limit $(NODES) \
	  distribute_ssh_keys.yml \
	  $(PLAYBOOK_PARAMETERS) \
	  -e @$(PRIVATE_VARS) --tags addusers $(V)

removeusers:  ## Remove user accounts
	ansible-playbook -i $(INVENTORY_FILE) --limit $(NODES) \
	  distribute_ssh_keys.yml \
	  $(PLAYBOOK_PARAMETERS) \
	  -e @$(PRIVATE_VARS) --tags removeusers $(V)

add:  ## Add keys
	ansible-playbook -i $(INVENTORY_FILE) --limit $(NODES) \
	  distribute_ssh_keys.yml \
	  $(PLAYBOOK_PARAMETERS) \
	  -e @$(PRIVATE_VARS) --tags add $(V)

remove:  ## Remove keys
	ansible-playbook -i $(INVENTORY_FILE) --limit $(NODES) \
	  distribute_ssh_keys.yml \
	  $(PLAYBOOK_PARAMETERS) \
	  -e @$(PRIVATE_VARS) --tags remove $(V)

help:  ## show this help.
	@echo "make targets:"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ": .*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo ""; echo "make vars (+defaults):"
	@grep -E '^[0-9a-zA-Z_-]+ \?=.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = " \\?= "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

echo_vars:
	@echo "Variables:"
	@echo $(PRIVATE_VARS)

list_tasks:
	ansible-playbook -i $(INVENTORY_FILE) --limit $(NODES) \
		distribute_ssh_keys.yml \
		$(PLAYBOOK_PARAMETERS) \
		-e @$(PRIVATE_VARS) --tags add --list-tasks