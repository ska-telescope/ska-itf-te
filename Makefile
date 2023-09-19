HELM_CHARTS_TO_PUBLISH=ska-mid-itf
PYTHON_VARS_AFTER_PYTEST= --disable-pytest-warnings
POETRY_CONFIG_VIRTUALENVS_CREATE = true

k8s-pre-install-chart:

VALUES ?= $(K8S_UMBRELLA_CHART_PATH)values.yaml
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
PYTHON_RUNNER = .venv/bin/python3 -m
PYTHON_LINE_LENGTH = 99
DOCS_SPHINXBUILD = .venv/bin/python3 -msphinx
PYTHON_TEST_FILE = tests/unit/ tests/functional/
PYTHON_SRC = ska_mid_itf
KUBE_NAMESPACE_SDP ?= $(KUBE_NAMESPACE)-sdp

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
INTEGRATION_TEST_ARGS = -v -r fEx --disable-pytest-warnings $(_MARKS) $(_COUNTS) $(EXIT) $(PYTEST_ADDOPTS) | tee pytest.stdout

ACCEPTANCE_TEST_SOURCE ?= submodules/.ska-sdp-integration/tests/integration/test_component_status.py
ACCEPTANCE_TEST_ARGS = -v -r fEx --disable-pytest-warnings $(_MARKS) $(_COUNTS) $(EXIT) $(PYTEST_ADDOPTS) | tee pytest.stdout

SDP_PARAMS ?= --set ska-sdp.helmdeploy.namespace=$(KUBE_NAMESPACE_SDP) \
	--set ska-sdp.ska-sdp-qa.zookeeper.clusterDomain=$(CLUSTER_DOMAIN) \
	--set ska-sdp.ska-sdp-qa.kafka.clusterDomain=$(CLUSTER_DOMAIN) \
	--set ska-sdp.ska-sdp-qa.redis.clusterDomain=$(CLUSTER_DOMAIN)

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
	$(TARANTA_PARAMS) \
	${K8S_TEST_TANGO_IMAGE_PARAMS} \
	${SKIP_TANGO_EXAMPLES_PARAMS} \
	$(K8S_EXTRA_PARAMS)

# # TODO: remove if no longer needed.
# -include resources/makefiles/itf-connect.mk

### USEFUL BITS FROM LOW
# better be verbose for debugging
PYTHON_VARS_AFTER_PYTEST ?= -v

python-post-lint:
	.venv/bin/mypy --config-file mypy.ini ska_mid_itf/ tests/

.PHONY: python-post-lint

DOCS_SPHINXOPTS=-n -W --keep-going

# Use the previously built image when running in the pipeline
# ifneq ($(CI_JOB_ID),)
# OCI_TAG = $(VERSION)-dev.c$(CI_COMMIT_SHORT_SHA)
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
						$(PYTHON_VARS_AFTER_PYTEST) ./tests/functional \
						 | tee pytest.stdout ## k8s-test test command to run in container
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

# include your own private variables for custom deployment configuration
-include PrivateRules.mak

# include namespace-specific targets
-include resources/makefiles/k8s-installs.mk

# include Xray uploads
include .make/xray.mk

XRAY_TEST_RESULT_FILE ?= build/reports/cucumber.json
XRAY_EXECUTION_CONFIG_FILE ?= tests/xray-config.json
XRAY_EXTRA_OPTS=-v

integration-test:
	@mkdir -p build
	$(PYTHON_RUNNER) pytest $(INTEGRATION_TEST_SOURCE) $(INTEGRATION_TEST_ARGS); \
	echo $$? > build/status


acceptance-test:
	@mkdir -p build
	$(PYTHON_RUNNER) pytest $(ACCEPTANCE_TEST_SOURCE) $(ACCEPTANCE_TEST_ARGS); \
	echo $$? > build/status

upload-to-confluence:
	@.venv/bin/upload-to-confluence sut_config.yaml build/reports/cucumber.json
	@echo "##### Results uploaded to https://confluence.skatelescope.org/x/arzVDQ #####"

template-chart: k8s-dep-update
	mkdir -p build
	helm template $(HELM_RELEASE) \
	$(K8S_CHART_PARAMS) \
	--debug \
	 $(K8S_UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE) > build/manifests.yaml

# use hook to create SDP namespace
k8s-pre-install-chart:
	@echo "k8s-pre-install-chart: creating the SDP namespace $(KUBE_NAMESPACE_SDP)"
	@make namespace-sdp KUBE_NAMESPACE=$(KUBE_NAMESPACE_SDP)

# use hook to create SDP namespace
k8s-pre-install-chart-car:
	@echo "k8s-pre-install-chart-car: creating the SDP namespace $(KUBE_NAMESPACE_SDP)"
	@make namespace-sdp KUBE_NAMESPACE=$(KUBE_NAMESPACE_SDP)

# use hook to delete SDP namespace
k8s-post-uninstall-chart:
	@echo "k8s-post-uninstall-chart: deleting the SDP namespace $(KUBE_NAMESPACE_SDP)"
	@make delete-sdp-namespace KUBE_NAMESPACE=$(KUBE_NAMESPACE_SDP)

namespace-sdp: KUBE_NAMESPACE := $(KUBE_NAMESPACE_SDP)
namespace-sdp: k8s-namespace
