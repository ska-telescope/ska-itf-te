.DEFAULT_GOAL := help

MKFILE_PATH := $(abspath $(firstword $(MAKEFILE_LIST)))
MKFILE_DIR := $(dir $(MKFILE_PATH))

# include makefile targets from the submodule
include $(MKFILE_DIR)../../.make/oci.mk

# include core make support
include $(MKFILE_DIR)../../.make/base.mk

# define overides for above variables in here
-include $(MKFILE_DIR)PrivateRules.mak


INVENTORY_TEMPLATE ?= $(MKFILE_DIR)inventory/hosts-template
INVENTORY_FILE ?= $(MKFILE_DIR)inventory/hosts
PLAYBOOK_PARAMETERS ?= ## any additional ansible tags can go here - see ansible-playbook --help
TEAM ?= atlas
TEAM_VARS_FILE ?= $(MKFILE_DIR)group_vars/$(TEAM)/$(TEAM).yml
ANSIBLE_COMMAND := ansible-playbook -i $(INVENTORY_FILE) -e @$(TEAM_VARS_FILE) $(PLAYBOOK_PARAMETERS) $(V)
ANSIBLE_COMMAND_DRY_RUN := $(ANSIBLE_COMMAND) --check --diff
V ?=
USER ?= $(shell whoami)

SPFRX_GOALS := setup_spfrx setup_spfrx_dry_run setup_spfrx_host setup_spfrx_host_dry_run validate_spfrx validate_spfrx_dry_run help long-help
ifneq ($(filter $(SPFRX_GOALS),$(MAKECMDGOALS)),)
AD_USER ?= $(USER)
endif

SERIAL ?= ## Serial number of the SPFRX unit (required for setup_spfrx targets; max 49 characters)

ifndef AD_USER
$(error AD_USER is not set: set this to your active directory user (i.e. Jira username.))
endif
export AD_USER

vars:  ## Variables
	@echo "Current variable settings:"
	@echo "INVENTORY_TEMPLATE=$(INVENTORY_TEMPLATE)"
	@echo "INVENTORY_FILE=$(INVENTORY_FILE)"
	@echo "PLAYBOOK_PARAMETERS=$(PLAYBOOK_PARAMETERS)"
	@echo "TEAM=$(TEAM)"
	@echo "TEAM_VARS_FILE=$(TEAM_VARS_FILE)"
	@echo "AD_USER=$(AD_USER)"
	@echo "ANSIBLE_COMMAND=$(ANSIBLE_COMMAND)"
	@echo "ANSIBLE_COMMAND_DRY_RUN=$(ANSIBLE_COMMAND_DRY_RUN)"
	@echo "V=$(V)"
.PHONY: vars

# Guard target: fails with a clear error if the named variable is unset.
guard-%:
	@if [ -z "$($(*))" ]; then echo "ERROR: $* is not set. Run 'make help' for usage."; exit 1; fi
.PHONY: guard-%

# Guard target: fails if SERIAL is unset or exceeds 49 characters.
guard-SERIAL:
	@if [ -z "$(SERIAL)" ]; then echo "ERROR: SERIAL is not set. Provide a serial number with SERIAL=..."; exit 1; fi
	@if [ $$(printf '%s' '$(SERIAL)' | wc -c) -ge 50 ]; then echo "ERROR: SERIAL must be less than 50 characters."; exit 1; fi
.PHONY: guard-SERIAL

# Guard target: fails if DISH_INDEX is unset or not a positive integer.
guard-DISH_INDEX:
	@if [ -z "$(DISH_INDEX)" ]; then echo "ERROR: DISH_INDEX is not set. Run 'make help' for usage."; exit 1; fi
	@if ! echo "$(DISH_INDEX)" | grep -qE '^[0-9]+$$'; then echo "ERROR: DISH_INDEX must be a numerical value."; exit 1; fi
.PHONY: guard-DISH_INDEX

setup: $(INVENTORY_FILE)

refresh_inventory: ## Regenerates the inventory file from the template.
	cp $(INVENTORY_TEMPLATE) $(INVENTORY_FILE)
	sed -i.x 's|<AD_USER>|$(AD_USER)|g' $(INVENTORY_FILE)
	sed -i.x 's|<USER>|$(USER)|g' $(INVENTORY_FILE)
	rm -f $(INVENTORY_FILE).x
.PHONY: refresh_inventory

setup_pi: setup ## Runs the full playbook against the Raspberry Pi.
	$(ANSIBLE_COMMAND) --limit raspberry_pi $(MKFILE_DIR)site.yml
.PHONY: setup_pi

setup_pi_dry_run: setup ## Runs the full playbook against the Raspberry Pi in dry-run mode.
	$(ANSIBLE_COMMAND_DRY_RUN) --limit raspberry_pi $(MKFILE_DIR)site.yml
.PHONY: setup_pi_dry_run

setup_spfrx: setup guard-DISH_INDEX guard-SERIAL## Runs the playbook against the SPFRX host for a given DISH_INDEX. Usage: make setup_spfrx DISH_INDEX=1
	@SPFRX_HOST=$$(awk '/dish_index=$(DISH_INDEX)([[:space:]]|$$)/{print $$1}' $(INVENTORY_FILE)); \
	if [ -z "$$SPFRX_HOST" ]; then \
		echo "No host with dish_index=$(DISH_INDEX) found. Adding spfrx$(DISH_INDEX) to [spfrx_mid]."; \
		printf 'spfrx$(DISH_INDEX) ansible_host=10.10.101.148 host_identifier="spfrx$(DISH_INDEX)" dish_index=$(DISH_INDEX) serial=${SERIAL}\n' >> $(INVENTORY_FILE); \
		SPFRX_HOST=spfrx$(DISH_INDEX); \
	fi; \
 	$(ANSIBLE_COMMAND) --ask-become-pass --limit $$SPFRX_HOST --tags spfrx $(MKFILE_DIR)site.yml
	sed -i.x -E "/dish_index=$(DISH_INDEX)([[:space:]]|$$)/s/ansible_host=[^[:space:]]*/ansible_host=10.160.$(DISH_INDEX).5/" $(INVENTORY_FILE)
	rm -f $(INVENTORY_FILE).x
.PHONY: setup_spfrx

setup_spfrx_dry_run: setup guard-DISH_INDEX guard-SERIAL ## Runs the playbook against the SPFRX host for a given DISH_INDEX in dry-run mode. Usage: make setup_spfrx_dry_run DISH_INDEX=1
	@SPFRX_HOST=$$(awk '/dish_index=$(DISH_INDEX)([[:space:]]|$$)/{print $$1}' $(INVENTORY_FILE)); \
	if [ -z "$$SPFRX_HOST" ]; then \
		echo "No host with dish_index=$(DISH_INDEX) found. Adding spfrx$(DISH_INDEX) to [spfrx_mid]."; \
		printf 'spfrx$(DISH_INDEX) ansible_host=10.10.101.148 host_identifier="spfrx$(DISH_INDEX)" dish_index=$(DISH_INDEX) serial=${SERIAL}\n' >> $(INVENTORY_FILE); \
		SPFRX_HOST=spfrx$(DISH_INDEX); \
	fi; \
	$(ANSIBLE_COMMAND_DRY_RUN) -e serial=$(SERIAL) --ask-become-pass --limit $$SPFRX_HOST --tags spfrx $(MKFILE_DIR)site.yml
	sed -i.x -E "/dish_index=$(DISH_INDEX)([[:space:]]|$$)/s/ansible_host=[^[:space:]]*/ansible_host=10.160.$(DISH_INDEX).5/" $(INVENTORY_FILE)
	rm -f $(INVENTORY_FILE).x
.PHONY: setup_spfrx_dry_run

validate_spfrx: setup guard-DISH_INDEX ## Runs the SPFRx validation tasks (post human intervention) for a given DISH_INDEX. Usage: make validate_spfrx DISH_INDEX=1
	@SPFRX_HOST=$$(awk '/^\[spfrx_mid\]/{f=1;next} /^\[/{f=0} f && /dish_index=$(DISH_INDEX)([[:space:]]|$$)/{print $$1; exit}' $(INVENTORY_FILE)); \
	if [ -z "$$SPFRX_HOST" ]; then \
		echo "ERROR: No host with dish_index=$(DISH_INDEX) found in the [spfrx_mid] group of $(INVENTORY_FILE)."; \
		exit 1; \
	fi; \
	$(ANSIBLE_COMMAND) --ask-become-pass --limit $$SPFRX_HOST --tags spfrx_validate $(MKFILE_DIR)site.yml
.PHONY: validate_spfrx

validate_spfrx_dry_run: setup guard-DISH_INDEX ## Runs the SPFRx validation tasks for a given DISH_INDEX in dry-run mode. Usage: make validate_spfrx_dry_run DISH_INDEX=1
	@SPFRX_HOST=$$(awk '/^\[spfrx_mid\]/{f=1;next} /^\[/{f=0} f && /dish_index=$(DISH_INDEX)([[:space:]]|$$)/{print $$1; exit}' $(INVENTORY_FILE)); \
	if [ -z "$$SPFRX_HOST" ]; then \
		echo "ERROR: No host with dish_index=$(DISH_INDEX) found in the [spfrx_mid] group of $(INVENTORY_FILE)."; \
		exit 1; \
	fi; \
	$(ANSIBLE_COMMAND_DRY_RUN) --ask-become-pass --limit $$SPFRX_HOST --tags spfrx_validate $(MKFILE_DIR)site.yml
.PHONY: validate_spfrx_dry_run

setup_spfrx_host: refresh_inventory guard-HOST ## Runs the playbook for a specific SPFRX host, with spfrx tags. Usage: make setup_spfrx_host HOST=spfrx03
	@if ! grep -qE "^$(HOST)[[:space:]]" $(INVENTORY_FILE); then echo "ERROR: No host '$(HOST)' found in $(INVENTORY_FILE)"; exit 1; fi; \
	$(ANSIBLE_COMMAND) --limit $(HOST) --tags spfrx $(MKFILE_DIR)site.yml
.PHONY: setup_spfrx_host

setup_spfrx_host_dry_run: refresh_inventory guard-HOST ## Runs the playbook for a specific SPFRX host with spfrx tags in dry-run mode. Usage: make setup_spfrx_host_dry_run HOST=spfrx03
	@if ! grep -qE "^$(HOST)[[:space:]]" $(INVENTORY_FILE); then echo "ERROR: No host '$(HOST)' found in $(INVENTORY_FILE)"; exit 1; fi; \
	$(ANSIBLE_COMMAND_DRY_RUN) --limit $(HOST) --tags spfrx $(MKFILE_DIR)site.yml
.PHONY: setup_spfrx_host_dry_run

setup_gaia: setup ## Runs the full playbook against Gaia.
	$(ANSIBLE_COMMAND) --limit gaia $(MKFILE_DIR)site.yml
.PHONY: setup_gaia

setup_gaia_dry_run: setup ## Runs the full playbook against Gaia in dry-run mode.
	$(ANSIBLE_COMMAND_DRY_RUN) --limit gaia $(MKFILE_DIR)site.yml
.PHONY: setup_gaia

setup_talon_boards: setup ## Runs the full playbook against the Talon boards.
	$(ANSIBLE_COMMAND) --limit talon $(MKFILE_DIR)site.yml
.PHONY: setup_talon

setup_talon_boards_dry_run: setup ## Runs the full playbook against the Talon boards in dry-run mode.
	$(ANSIBLE_COMMAND_DRY_RUN) --limit talon $(MKFILE_DIR)site.yml
.PHONY: setup_talon_boards_dry_run

setup_local_ssh_config: setup ## Sets up your localhost for using the ansible playbooks.
	$(ANSIBLE_COMMAND) --limit localhost $(MKFILE_DIR)site.yml
.PHONY: setup_local_ssh_config

setup_local_ssh_config_dry_run: setup ## Sets up your localhost for using the ansible playbooks (dry-run mode).
	$(ANSIBLE_COMMAND_DRY_RUN) --limit localhost $(MKFILE_DIR)site.yml
.PHONY: setup_local_ssh_config_dry_run

$(INVENTORY_FILE): $(INVENTORY_TEMPLATE) # Sets up the inventory file with the correct user variables. Make sure you have AD_USER set.
	$(MAKE) refresh_inventory

lint: ## Lint check playbook
	uv run ansible-lint -v -c $(MKFILE_DIR).ansible-lint $(MKFILE_DIR)site.yml
.PHONY: lint

test: test-default test-gaia test-raspberry_pi ## Runs all playbook tests.
.PHONY: test

test-default: ## Runs a playbook test with all flags enabled.
	$(MKFILE_DIR)testing/run.sh ansible-test-default default
.PHONY: test-default

test-gaia: ## Runs a playbook test as if it were against Gaia.
	$(MKFILE_DIR)testing/run.sh ansible-test-gaia gaia
.PHONY: test-gaia

test-raspberry_pi: ## Runs a playbook test as if it were against the Raspberry Pi.
	$(MKFILE_DIR)testing/run.sh ansible-test-default raspberry_pi
.PHONY: test-raspberry_pi

test-cicd: test-cicd-default test-cicd-gaia test-cicd-raspberry_pi ## Runs all playbook tests (intended for Gitlab pipelines).
.PHONY: test-cicd

# TEST_HOST is the name of the service started up in the pipeline.
# See the ansible-test job in the .gitlab-ci.yml.
test-cicd-default: TEST_HOST := ansible-test-default ## Runs a playbook test with all flags enabled (intended for Gitlab pipelines).
test-cicd-default:
	$(MKFILE_DIR)testing/test.sh default
.PHONY: test-cicd-default

test-cicd-gaia: TEST_HOST := ansible-test-gaia ## Runs a playbook test as if it were against Gaia (intended for Gitlab pipelines).
test-cicd-gaia:
	$(MKFILE_DIR)testing/test.sh gaia
.PHONY: test-cicd-gaia

test-cicd-raspberry_pi: TEST_HOST := ansible-test-raspberry-pi ## Runs a playbook test as if it were against the Raspberry Pi (intended for Gitlab pipelines).
test-cicd-raspberry_pi:
	$(MKFILE_DIR)testing/test.sh raspberry_pi
.PHONY: test-cicd-raspberry_pi

list_tasks: ## Prints the tasks to be executed during a playbook run.
	ansible-playbook -i $(INVENTORY_FILE) \
		$(MKFILE_DIR)site.yml \
		$(PLAYBOOK_PARAMETERS) \
		--list-tasks
.PHONY: list_tasks

HELP_FILTER_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
HELP_FILTER_PATTERN := $(firstword $(HELP_FILTER_ARGS))

# Note: in order for a target to show up in the help message,
# it needs to have a comment starting with '##' on the same line.
help:  ## Show this help (optional filter: make help spfrx).
	@echo ""; echo "$(HELP_POWDER_BLUE)SECTION:$(HELP_NORMAL) ansible-playbooks"; \
	echo "$(HELP_GREEN)MAKE TARGETS:$(HELP_NORMAL)"; \
	if [ -n "$(HELP_FILTER_PATTERN)" ]; then \
		grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MKFILE_PATH) | grep "$(HELP_FILTER_PATTERN)" | sort | awk 'BEGIN {FS = ": .*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'; \
	else \
		grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MKFILE_PATH) | sort | awk 'BEGIN {FS = ": .*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'; \
	fi; \
	echo ""; echo "$(HELP_YELLOW)MAKE VARS (+defaults):$(HELP_NORMAL)"; \
	if [ -n "$(HELP_FILTER_PATTERN)" ]; then \
		grep -E '^[0-9a-zA-Z_-]+ \?=.*$$' $(MKFILE_PATH) | grep "$(HELP_FILTER_PATTERN)" | sort | awk 'BEGIN {FS = " \\?= "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' || true; \
	else \
		grep -E '^[0-9a-zA-Z_-]+ \?=.*$$' $(MKFILE_PATH) | sort | awk 'BEGIN {FS = " \\?= "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' || true; \
	fi
.PHONY: help

echo_vars:
	@echo "Variables:"
	@echo $(PRIVATE_VARS)
.PHONY: echo_vars
