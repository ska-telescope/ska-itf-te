INVENTORY_FILE ?= ./variables/inventory
PLAYBOOK_PARAMETERS ?= ## any additional ansible tags can go here - see ansible-playbook --help
NODES ?= nodes ## subset of hosts from inventory to run against
V ?=
GAIA_IP ?= 10.165.3.7
PI_IP ?= 10.165.3.11

.DEFAULT_GOAL := help

# define overides for above variables in here
-include PrivateRules.mak

vars:  ## Variables
	@echo "Current variable settings:"
	@echo "PRIVATE_VARS=$(PRIVATE_VARS)"
	@echo "INVENTORY_FILE=$(INVENTORY_FILE)"
	@echo "PLAYBOOK_PARAMETERS=$(PLAYBOOK_PARAMETERS)"
	@echo "NODES=$(NODES)"
	@echo "SSH_USER=$(SSH_USER)"

all: addkey removekey

connect: ## Add SSH Forwarding to local machine and SSH into Gaia
	@echo "Connecting to the Gaia as $(SSH_USER)";
	@echo "###########################################";
	ssh -A $(SSH_USER)@$(GAIA_IP);
	@echo "Welcome back"; \

connect_pi: ## Add SSH Forwarding to local machine and SSH into Gaia
	@echo "Connecting to the Raspberry Pi as $(SSH_USER)";
	@echo "###########################################";
	ssh -A $(SSH_USER)@$(PI_IP);
	@echo "Welcome back"; \

lint: ## Lint check playbook
	ansible-lint -vvv distribute_ssh_keys.yml

setup_pi:
	ansible-playbook -i $(INVENTORY_FILE) --limit $(NODES) \
	  main.yml \
	  $(PLAYBOOK_PARAMETERS) \
	  -u=$(SUDO_USER) \
	  --extra-vars "user_name=$(ACTUAL_USER) createuser=true addkey=true" \
	  $(V)

setup_gaia:
	ansible-playbook -i $(INVENTORY_FILE) --limit $(NODES) \
	  main.yml \
	  $(PLAYBOOK_PARAMETERS) \
	  -u=$(SUDO_USER) \
	  --extra-vars "user_name=$(ACTUAL_USER) addkey=true" \
	  $(V)

adduser:  ## Create user accounts
	ansible-playbook -i $(INVENTORY_FILE) --limit $(NODES) \
	  distribute_ssh_keys.yml \
	  $(PLAYBOOK_PARAMETERS) \
	  -e @$(PRIVATE_VARS) --tags adduser $(V)

removeuser:  ## Remove user accounts
	ansible-playbook -i $(INVENTORY_FILE) --limit $(NODES) \
	  main.yml \
	  $(PLAYBOOK_PARAMETERS) \
	  --extra-vars "removeuser=true" $(V)

addkey:  ## Add keys
	ansible-playbook -i $(INVENTORY_FILE) --limit $(NODES) \
	  distribute_ssh_keys.yml \
	  $(PLAYBOOK_PARAMETERS) \
	  -e @$(PRIVATE_VARS) --tags addkey $(V)

removekey:  ## Remove keys
	ansible-playbook -i $(INVENTORY_FILE) --limit $(NODES) \
	  distribute_ssh_keys.yml \
	  $(PLAYBOOK_PARAMETERS) \
	  -e @$(PRIVATE_VARS) --tags removekey $(V)

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