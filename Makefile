# include your own private variables for custom deployment configuration
-include PrivateRules.mak

OCI_BUILD_ADDITIONAL_ARGS += --cache-from registry.gitlab.com/ska-telescope/ska-mid-itf/ska-mid-itf-base:0.1.4

HELM_CHARTS_TO_PUBLISH=ska-mid-itf
PYTHON_VARS_AFTER_PYTEST= --disable-pytest-warnings
POETRY_CONFIG_VIRTUALENVS_CREATE = true

# VALUES ?= $(K8S_UMBRELLA_CHART_PATH)values.yaml
XAUTHORITY ?= $(HOME)/.Xauthority
THIS_HOST := $(shell ip a 2> /dev/null | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p' | head -n1)
DISPLAY ?= $(THIS_HOST):0
JIVE ?= false# Enable jive
TARANTA ?= false# Enable Taranta
MINIKUBE ?= true ## Minikube or not
EXPOSE_All_DS ?= true ## Expose All Tango Services to the external network (enable Loadbalancer service)
SKA_TANGO_OPERATOR ?= true
EXPOSE_DATABASE_DS ?= true## 
TANGO_DATABASE_DS ?= tango-databaseds## TANGO_DATABASE_DS name
TANGO_HOST ?= tango-databaseds:10000## TANGO_HOST connection to the Tango DS
TANGO_SERVER_PORT ?= 45450## TANGO_SERVER_PORT - fixed listening port for local server
CLUSTER_DOMAIN = miditf.internal.skao.int## Domain used for naming Tango Device Servers
INGRESS_HOST = k8s.$(CLUSTER_DOMAIN)## Tango host, cluster domain, what are all these things???
ITANGO_ENABLED ?= true## ITango enabled in ska-tango-base
PYTHON_RUNNER = poetry run python3 -m
PYTHON_LINE_LENGTH = 99
DOCS_SPHINXBUILD = poetry run python3 -msphinx
PYTHON_TEST_FILE = tests/unit/ tests/functional/
PYTHON_LINT_TARGET ?= tests/
SPFRX_CONSOLE_VER ?= 0.0.1 # Set this value in the Gitlab Environment - this value should fail
ifneq ($(COUNT),)
# Dashcount is a synthesis of testcount as input user variable and is used to
# run a paricular test/s multiple times. If no testcount is set then the entire
# --count option is removed
_COUNT ?= --count=$(COUNT)
else
_COUNT ?= 
endif

MARKS ?=## Additional Marks to add to pytests
# Dishmark is a synthesis of marks to add to test, it will always start with the tests for the appropriate
# telescope (e.g. TEL=mid or TEL=low) thereafter followed by additional filters
ifneq ($(ADDMARKS),)
_MARKS ?= -, $(MARKS)
else
_MARKS ?= 
endif
EXIT_AT_FAIL ?=True## whether the pytest should exit immediately upon failure
ifneq ($(EXIT_AT_FAIL),false)
EXIT = -x
else
EXIT = 
endif

INTEGRATION_TEST_SOURCE ?= tests/integration
INTEGRATION_TEST_ARGS = -v -r fEx --disable-pytest-warnings $(_MARKS) $(_COUNTS) $(EXIT) $(PYTEST_ADDOPTS)

DISH_LMC_INITIAL_PARAMS ?=
DISH_LMC_EXTRA_PARAMS ?=

ifneq ($(DISH_ID),)
DISH_LMC_EXTRA_PARAMS = --set global.dish_id=$(DISH_ID) \
	--set global.tangodb_fqdn=$(TANGO_DATABASE_DS).$(KUBE_NAMESPACE).svc.$(CLUSTER_DOMAIN) \
	--set global.tango_host=$(TANGO_HOST) \
	--set global.tangodb_port=10000
endif

SPFRX_IN_THE_LOOP ?= #Boolean flag to control deployment of the device described in SPFRX_TANGO_INSTANCE, SPFRX_ADDRESS variables
SPFRX_FAMILY_NAME ?= spfrxpu
SPFRX_MEMBER_NAME ?= controller
ifeq ($(SPFRX_IN_THE_LOOP), true)
	SPFRX_SIM_ENABLE := false
else
	SPFRX_SIM_ENABLE := true
endif
SPFRX_TRL ?= $(DISH_ID)/$(SPFRX_FAMILY_NAME)/$(SPFRX_MEMBER_NAME)

SPFRX_ADDRESS ?=localhost
SPFRX_BIN ?=/usr/local/bin 
SPFRX_LOCAL_DIR ?=artifacts
SPFRX_SCRIPTS_DIR ?=scripts
SPFRX_TANGO_INSTANCE ?=this-one
SPFRX_TANGO_LOGGING_LEVEL ?=4

ifeq ($(SPFRX_IN_THE_LOOP), true)
	DISH_LMC_EXTRA_PARAMS += \
	--set spfrx.enabled=true \
	--set spfrx.console.version=$(SPFRX_CONSOLE_VER) \
	--set spfrx.address=$(SPFRX_ADDRESS) \
	--set spfrx.bin=$(SPFRX_BIN) \
	--set spfrx.local_dir=$(SPFRX_LOCAL_DIR) \
	--set spfrx.scripts_dir=$(SPFRX_SCRIPTS_DIR) \
	--set spfrx.instance=$(SPFRX_TANGO_INSTANCE) \
	--set spfrx.logging_level=$(SPFRX_TANGO_LOGGING_LEVEL) \
	--set dishlmc.ska-mid-dish-manager.dishmanager.spfrx.fqdn=$(SPFRX_TRL) \
	--set dishlmc.ska-mid-dish-simulators.deviceServers.spfrxdevice.enabled=$(SPFRX_SIM_ENABLE)
endif

ifeq ($(DISH_ID), ska001)
	DISH_LMC_EXTRA_PARAMS += -f charts/dish-lmc/values-cetc.yaml \
	--set dishlmc.ska-mid-dish-ds-manager.dishstructuremanager.dsSim.fqdn=$(DS_SIM_OPCUA_FQDN)
endif

DISH_LMC_PARAMS ?= $(DISH_LMC_INITIAL_PARAMS) $(DISH_LMC_EXTRA_PARAMS)

SKUID_URL ?= ska-ser-skuid-test-svc.$(KUBE_NAMESPACE).svc.$(CLUSTER_DOMAIN):9870
ODA_PARAMS ?= --set ska-db-oda-umbrella.ska-db-oda.rest.skuid.url=$(SKUID_URL)

SDP_PARAMS ?= --set sdp.helmdeploy.namespace=$(KUBE_NAMESPACE_SDP) \
	--set sdp.ska-sdp-qa.zookeeper.clusterDomain=$(CLUSTER_DOMAIN) \
	--set sdp.kafka.clusterDomain=$(CLUSTER_DOMAIN) \
	--set sdp.ska-sdp-qa.redis.clusterDomain=$(CLUSTER_DOMAIN) \
	--set global.sdp.processingNamespace=$(KUBE_NAMESPACE_SDP)

K8S_CHART_PARAMS ?= --set global.minikube=$(MINIKUBE) \
	--set global.exposeAllDS=$(EXPOSE_All_DS) \
	--set global.exposeDatabaseDS=$(EXPOSE_DATABASE_DS) \
	--set global.tango_host=$(TANGO_HOST) \
	--set global.device_server_port=$(TANGO_SERVER_PORT) \
	--set global.cluster_domain=$(CLUSTER_DOMAIN) \
	--set global.labels.app=$(KUBE_APP) \
	--set global.operator=$(SKA_TANGO_OPERATOR) \
	--set ska-tango-base.display=$(DISPLAY) \
	--set ska-tango-base.xauthority=$(XAUTHORITY) \
	--set ska-tango-base.jive.enabled=$(JIVE) \
	--set ska-tango-base.itango.enabled=$(ITANGO_ENABLED) \
	$(SDP_PARAMS) \
	$(ODA_PARAMS) \
	$(DISH_LMC_PARAMS) \
	$(TARANTA_PARAMS) \
	${K8S_TEST_TANGO_IMAGE_PARAMS} \
	${SKIP_TANGO_EXAMPLES_PARAMS} \
	$(K8S_EXTRA_PARAMS)

TMC_VALUES_PATH=charts/system-under-test/tmc-values.yaml
ifneq ("$(wildcard $(TMC_VALUES_PATH))","")
	K8S_EXTRA_PARAMS+=-f $(TMC_VALUES_PATH)
endif


# # TODO: remove if no longer needed.
# -include resources/makefiles/itf-connect.mk

### USEFUL BITS FROM LOW
# better be verbose for debugging
PYTHON_VARS_AFTER_PYTEST ?= -v

# Assume the project root is the directory of the top-level Makefile
PROJECT_ROOT := $(dir $(abspath $(firstword $(MAKEFILE_LIST))))

DOCS_SPHINXOPTS=-n -W --keep-going

# Use the previously built image when running in the pipeline
# ifneq ($(CI_JOB_ID),)
# # OCI_TAG = $(VERSION)-dev.c$(CI_COMMIT_SHORT_SHA)
# OCI_TAG = $(VERSION)-dev.c42d4ef0f # fix to specific dev tag
# CI_REGISTRY ?= registry.gitlab.com

# # for k8s-test
# K8S_TEST_IMAGE_TO_TEST=$(CI_REGISTRY)/ska-telescope/$(NAME)/$(NAME):$(OCI_TAG)
# endif

# https://github.com/pytest-dev/pytest-bdd/issues/401
PYTHON_VARS_BEFORE_PYTEST = PYTHONDONTWRITEBYTECODE=True

# better be verbose for debugging
PYTHON_VARS_AFTER_PYTEST ?= -v

# Add cucumber/json reports only for this test
ifeq ($(MAKECMDGOALS),k8s-test)
# execute in truel context; add BDD test results to be uploaded to xray
PYTHON_VARS_AFTER_PYTEST += --true-context --cucumberjson=build/reports/cucumber.json \
	--json-report --json-report-file=build/reports/report.json

# hack out PYTHONPATH - why is it even there?
# hack in test target directory
K8S_TEST_TEST_COMMAND = unset PYTHONPATH; TANGO_HOST=$(TANGO_HOST) \
						pytest \
						$(PYTHON_VARS_AFTER_PYTEST) ./tests/functional
endif

PING_HOST=itf-gateway# set this up in your /etc/hosts file from the Confluence page describing all the hosts.

itf-check-te-hosts-online:
	@ping -c 1 -t 2 $(PING_HOST); RC=$$?; \
		if [[ $$RC != 0 ]]; then \
		echo "Check VPN connection or setup your local DNS to reach the Gateway." && \
		exit $$RC; \
		else echo "Able to reach the Gateway host."; \
		echo "###############################"; echo; \
		fi;
	@python resources/ping-itf-hosts.py

check: itf-check-te-hosts-online

theres-a-ghost: 
	@kubectl get nodes -o=jsonpath="{.items[*]['metadata.name', 'status.capacity']}{'\n'}" | grep skao.int 

spooky: itf-spookd-install theres-a-ghost

ghostbusters: itf-spookd-uninstall

# include makefile targets from the submodule
include .make/oci.mk

# include k8s support
include .make/k8s.mk

# include Helm Chart support
include .make/helm.mk

# Include Python support
include .make/python.mk

# include raw support
include .make/raw.mk

# include core make support
include .make/base.mk

# include namespace-specific targets
-include resources/makefiles/k8s-installs.mk

# include CBF configuration targets
-include resources/makefiles/cbf-config.mk

# include Xray uploads
include .make/xray.mk

XRAY_TEST_RESULT_FILE ?= build/reports/cucumber.json
XRAY_EXECUTION_CONFIG_FILE ?= tests/xray-config.json
XRAY_EXTRA_OPTS=-v

integration-test:
	@mkdir -p build
	set -o pipefail; $(PYTHON_RUNNER) pytest $(INTEGRATION_TEST_SOURCE) $(INTEGRATION_TEST_ARGS); \
	echo $$? > build/status

upload-to-confluence:
	@poetry run upload-to-confluence sut_config.yaml build/reports/cucumber.json
	@echo "##### Results uploaded to https://confluence.skatelescope.org/x/arzVDQ #####"

k8s-template-chart-with-build-artifacts:
	@make k8s-template-chart > template.log
	@mkdir -p build
	@mv manifests.yaml build/manifests.yaml
	@echo "Find the chart template used to deploy all the things in the job artefacts - look for manifests.yaml."

.PHONY: k8s-template-chart-with-build-artifacts

env:
	env