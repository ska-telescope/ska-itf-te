# include your own private variables for custom deployment configuration
-include PrivateRules.mak

OCI_BUILD_ADDITIONAL_ARGS += --cache-from registry.gitlab.com/ska-telescope/ska-mid-itf/ska-mid-itf-base:0.1.4

HELM_CHARTS_TO_PUBLISH=ska-mid ska-mid-itf-ghosts ska-mid-cbf-engineering-console-cache
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
PYTHON_SWITCHES_FOR_FLAKE8 += --extend-ignore=F824

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
	_MARKS ?= -m $(MARKS)
	_SMOKE_TEST_MARKS ?= -m "$(SMOKE_TEST_MARKS)"
else
_MARKS ?=
_SMOKE_TEST_MARKS ?=
endif
EXIT_AT_FAIL ?=True## whether the pytest should exit immediately upon failure
ifneq ($(EXIT_AT_FAIL),false)
EXIT = -x
else
EXIT = 
endif

INTEGRATION_TEST_SOURCE ?= tests/integration
INTEGRATION_TEST_ARGS = -v -r fEx --disable-pytest-warnings $(_MARKS) $(_COUNTS) $(EXIT) $(PYTEST_ADDOPTS)

SMOKE_TEST_ARGS = -v -r fEx --disable-pytest-warnings $(_SMOKE_TEST_MARKS) $(_COUNTS) $(EXIT) $(PYTEST_ADDOPTS)

TMC_PARAMS ?=
ifeq ($(DISH_LMC_IN_THE_LOOP),true)
TMC_PARAMS += --set ska-tmc-mid.deviceServers.mocks.enabled=false \
	--set ska-tmc-mid.deviceServers.mocks.dish=false
endif

DISH_LMC_INITIAL_PARAMS ?=
DISH_LMC_EXTRA_PARAMS ?=
DISH_LMC_EDA_PARAMS ?=

ifneq ($(DISH_ID),)
DISH_LMC_EXTRA_PARAMS = \
	--set global.dish_id=$(DISH_ID) \
	--set global.tangodb_fqdn=$(TANGO_DATABASE_DS).$(KUBE_NAMESPACE).svc.$(CLUSTER_DOMAIN) \
	--set global.tango_host=$(TANGO_HOST) \
	--set global.tangodb_port=10000
endif

#TEMPORARY COMMIT - REMOVE --set ska-mid-dish-spfc-deployer.enabled=false LINE AS SOON AS SPFC DEPLOYER IS UPDATED & RELEASED)
SPFC_IN_THE_LOOP ?= #Boolean flag to control deployment of the SPFC Tango device in a Dish
SPFC_INSTANCE ?= that_one #Default value that needs to be overwritten during deployment
ifeq ($(SPFC_IN_THE_LOOP), true)
	DISH_LMC_EXTRA_PARAMS += \
	--set ska-dish-lmc.ska-mid-dish-simulators.deviceServers.spfdevice.enabled=false \
	--set ska-dish-lmc.ska-mid-dish-manager.dishmanager.spf.fqdn=$(DISH_ID)/spf/spfc \
	--set ska-mid-dish-spfc-deployer.global.dish_id=$(DISH_ID) \
	--set ska-mid-dish-spfc-deployer.enabled=true \
	--set ska-mid-dish-spfc-deployer.namespace=$(KUBE_NAMESPACE) \
	--set ska-mid-dish-spfc-deployer.instance=$(SPFC_INSTANCE) \
	--set ska-mid-dish-spfc-deployer.ip_address=$(SPFC_IP_ADDRESS) \
	--set ska-mid-dish-spfc-deployer.user=$(SPFC_USER) \
	--set ska-mid-dish-spfc-deployer.private_key=$(SPFC_PRIVATE_KEY) \
	--set ska-mid-dish-spfc-deployer.use_tango_db=$(USE_TANGO_DB) \
	--set ska-mid-dish-spfc-deployer.update_firmware=$(UPDATE_FIRMWARE) \
	--set ska-mid-dish-spfc-deployer.spfc_simulated_mode=$(SPFC_SIMULATED_MODE) \
	--set ska-mid-dish-spfc-deployer.artefact_token=$(ARTEFACT_TOKEN) \
	--set ska-mid-dish-spfc-deployer.dns_service=$(DNS_SERVICE) \
	--set global.cluster_domain=$(CLUSTER_DOMAIN)
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
	--set ska-mid-dish-spfrx-talondx-console.enabled=true \
	--set ska-mid-dish-spfrx-talondx-console.address=$(SPFRX_ADDRESS) \
	--set ska-mid-dish-spfrx-talondx-console.bin=$(SPFRX_BIN) \
	--set ska-mid-dish-spfrx-talondx-console.local_dir=$(SPFRX_LOCAL_DIR) \
	--set ska-mid-dish-spfrx-talondx-console.scripts_dir=$(SPFRX_SCRIPTS_DIR) \
	--set ska-mid-dish-spfrx-talondx-console.instance=$(SPFRX_TANGO_INSTANCE) \
	--set ska-mid-dish-spfrx-talondx-console.logging_level=$(SPFRX_TANGO_LOGGING_LEVEL) \
	--set ska-dish-lmc.ska-mid-dish-manager.dishmanager.spfrx.fqdn=$(SPFRX_TRL) \
	--set ska-dish-lmc.ska-mid-dish-simulators.deviceServers.spfrxdevice.enabled=$(SPFRX_SIM_ENABLE)
endif

CBF_HW_IN_THE_LOOP ?= 
CSP_PARAMS ?=
ifeq ($(CBF_HW_IN_THE_LOOP),true)
	CSP_PARAMS += --set ska-mid-cbf-engineering-console.enabled=true
endif

DISH_LMC_PARAMS ?= $(DISH_LMC_INITIAL_PARAMS) $(DISH_LMC_EXTRA_PARAMS) $(DISH_LMC_EDA_PARAMS)

SKUID_URL ?= ska-ser-skuid-test-svc.$(KUBE_NAMESPACE).svc.$(CLUSTER_DOMAIN):9870
ODA_PARAMS ?= --set ska-db-oda-umbrella.ska-db-oda.rest.skuid.url=$(SKUID_URL)

###################################################################
### THIS SECTION NEEDS REVIEW FROM SDP ARCHITECTS
SDP_EXTRA_PARAMS ?=
DPD_PARAMS ?= 

ifeq ($(KUBE_APP),ska-mid-itf-dpd)
	DPD_PARAMS += \
	--set global.ska-sdp.processingNamespace=$(KUBE_NAMESPACE_SDP)
endif

ifneq ($(DPD_PVC_NAME),)
	SDP_EXTRA_PARAMS += \
	--set ska-dataproduct-dashboard.dataProductPVC.name=$(DPD_PVC_NAME) \
	--set global.data-product-pvc-name=$(DPD_PVC_NAME)
endif

ifeq ($(KUBE_NAMESPACE),staging)
# Note that this create.enabled, should use the shared volume and link to
# that one, and not create a new PVC on the storage layer.
# Values are based on:
# - https://developer.skao.int/en/latest/howto/shared-storage.html
# - https://gitlab.com/ska-telescope/sdp/ska-sdp-integration/-/blob/0.21.0/charts/ska-sdp/templates/pvc.yaml
	SDP_EXTRA_PARAMS += \
		--set global.data-product-pvc-name=staging-pvc \
		--set ska-dataproduct-dashboard.dataProductPVC.name=staging-pvc \
		--set ska-sdp.data-pvc.create.clone-pvc=staging-pvc \
		--set ska-sdp.data-pvc.create.clone-pvc-namespace=shared-ska-dataproducts \
		--set ska-sdp.data-pvc.create.enabled=true \
		--set ska-sdp.data-pvc.create.size=2Ti \
		--set ska-sdp.data-pvc.create.storageClassName=ceph-cephfs \
		--set ska-sdp.data-pvc.pod.enabled=true
endif

# ifeq (wildcard($(KUBE_NAMESPACE),"ci-*")) # This will break - fix before push! block to be used in automated testing
# 	SDP_EXTRA_PARAMS += \
# 	--set global.data-product-pvc-name=$(DPD_PVC_NAME)
#   --set ska-sdp.data-pvc.create=true # check syntax for this one
# endif

SDP_PARAMS ?= --set ska-sdp.helmdeploy.namespace=$(KUBE_NAMESPACE_SDP) \
	--set ska-sdp.ska-sdp-qa.zookeeper.clusterDomain=$(CLUSTER_DOMAIN) \
	--set ska-sdp.kafka.clusterDomain=$(CLUSTER_DOMAIN) \
	--set ska-sdp.ska-sdp-qa.redis.clusterDomain=$(CLUSTER_DOMAIN) \
	--set global.sdp.processingNamespace=$(KUBE_NAMESPACE_SDP) \
	$(SDP_EXTRA_PARAMS)

###################################################################

###################################################################
### TODO: Move creds to Vault
EDA_EXTRA_PARAMS ?=
EDA_PARAMS ?= --set ska-tango-archiver.dbpassword=${EDA_DB_PASSWORD} \
	--set ska-tango-archiver.archviewer.instances[0].timescale_login=admin:${EDA_DB_PASSWORD} \
	$(EDA_EXTRA_PARAMS)
###################################################################

K8S_TEST_RUNNER_PARAMS ?=

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
	$(K8S_EXTRA_PARAMS) \
	$(K8S_TEST_RUNNER_PARAMS) \
	$(TMC_PARAMS) \
	$(CSP_PARAMS) \
	$(EDA_PARAMS) \
	$(SUT_ENABLERS) \
	$(DISH_ENABLERS) \
	$(ODA_ENABLERS) \
	$(DPD_ENABLERS) \


TMC_VALUES_PATH?=charts/ska-mid/tmc-values.yaml
ifneq ("$(wildcard $(TMC_VALUES_PATH))","")
	K8S_EXTRA_PARAMS+=-f $(TMC_VALUES_PATH)
endif
ifneq ("$(wildcard $(SUT_CHART_DIR))","")
	K8S_EXTRA_PARAMS+=-f charts/ska-mid/values.yaml
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
# execute in true context; add BDD test results to be uploaded to xray
PYTHON_VARS_AFTER_PYTEST += --true-context --cucumberjson=build/reports/cucumber.json \
	--json-report --json-report-file=build/reports/report.json

# hack out PYTHONPATH - why is it even there?
# hack in test target directory
K8S_TEST_TEST_COMMAND = unset PYTHONPATH; TANGO_HOST=$(TANGO_HOST) \
						pytest \
						$(PYTHON_VARS_AFTER_PYTEST) ./tests/functional
endif

PING_HOST=itf-gateway# set this up in your /etc/hosts file from the Confluence page describing all the hosts under Management Network section

itf-check-te-hosts-online:
	@ping -c 1 -t 2 $(PING_HOST); RC=$$?; \
		if [[ $$RC != 0 ]]; then \
		echo "Check VPN connection or setup your local DNS to reach the Gateway." && \
		exit $$RC; \
		else echo "Able to reach the Gateway host."; \
		echo "###############################"; echo; \
		fi;
	@python3 resources/ping-itf-hosts.py

check: itf-check-te-hosts-online

theres-a-ghost: 
	@kubectl get nodes -o=jsonpath="{.items[*]['metadata.name', 'status.capacity']}{'\n'}" | grep skao.int 

spooky: itf-spookd-install theres-a-ghost

ghostbusters: itf-spookd-uninstall

# include core make support
include .make/base.mk

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

# include namespace-specific targets
-include resources/makefiles/k8s-installs.mk

# include CBF configuration targets
-include resources/makefiles/cbf-config.mk

# include Taranta multiDB targets
-include resources/makefiles/taranta.mk

# include Xray uploads
include .make/xray.mk

# include logging tools
include resources/makefiles/logs.mk

# include Telescope Model targets
include .make/tmdata.mk


XRAY_TEST_RESULT_FILE ?= build/reports/cucumber.json
XRAY_EXECUTION_CONFIG_FILE ?= tests/xray-config.json
XRAY_EXTRA_OPTS=-v

CLUSTER_HEADLAMP_BASE_URL?=https://k8s.miditf.internal.skao.int/headlamp
CLUSTER_DATACENTRE?=mid-itf
CLUSTER_MONITOR?=mid-itf-monitor

integration-test: k8s-info
	@mkdir -p build
	set -o pipefail; $(PYTHON_RUNNER) pytest $(INTEGRATION_TEST_SOURCE) $(INTEGRATION_TEST_ARGS); \
	echo $$? > build/status
	@mv sequence-diagram.puml build/sequence-diagram.puml 2>/dev/null || echo "sequence diagram not moved"

upload-to-confluence:
	@poetry run upload-to-confluence sut_config.yaml build/reports/cucumber.json

get-deployment-config-info:
	@helm -n $(KUBE_NAMESPACE) get values $(HELM_RELEASE)
	@make k8s-template-chart > template.log
	@mkdir -p build
	@mv manifests.yaml build/manifests.yaml
	@echo "Find the chart template used to deploy all the things in the job artefacts - look for manifests.yaml."

.PHONY: get-deployment-config-info

env:
	env

post-set-release:
	@CURRENT_RELEASE=$$(awk -F= '/^release=/{print $$2}' .release); \
	./scripts/release/update_chart_version.sh $$CURRENT_RELEASE sut_config.yaml; \
	./scripts/release/update_testing_image_tag.sh $$CURRENT_RELEASE charts/ska-mid-testing/values.yaml; \
	echo "Updated SUT Config graph reflecting Mid ITF latest version."

print-telescope-state:
	@poetry run telescope_state_control --print-state -n ${E2E_TEST_EXECUTION_NAMESPACE} -d "${DISH_IDS}"

teardown-telescope:
	@poetry run telescope_state_control --teardown -n ${E2E_TEST_EXECUTION_NAMESPACE} -d "${DISH_IDS}"

teardown-telescope-to-pre-assign:
	@poetry run telescope_state_control --teardown -n ${E2E_TEST_EXECUTION_NAMESPACE} -d "${DISH_IDS}" -c "ON" -b "STANDBY_FP"

test-e2e-kapb:
	infra use za-aa-k8s-master01-k8s
	kubectl delete job test-job -n integration-tests || true
	@CWD=$$(pwd) \
	  KUBE_NAMESPACE=integration-tests \
	  HELM_RELEASE=testing  \
	  K8S_UMBRELLA_CHART_PATH=$$CWD/charts/ska-mid-testing \
	  K8S_CHARTS=$$CWD/charts/ska-mid-testing \
	  make k8s-template-chart > /dev/null 2>&1
	@yq eval-all 'select(.kind == "Job" and .metadata.name == "test-job")' manifests.yaml > test-job.yaml
	kubectl apply -f test-job.yaml
	kubectl wait jobs -n integration-tests -l job-name=test-job --for=condition=complete --timeout="180s"
	@echo "Test job completed"
	@rm test-job.yaml manifests.yaml || true
	
smoke-tests:
	set -o pipefail; $(PYTHON_RUNNER) pytest $(SMOKE_TEST_SOURCE) $(SMOKE_TEST_ARGS) --log-cli-level=INFO;
	mkdir -p build
	echo $$? > build/status

k8s-file-copy:
	kubectl cp -n ${COPY_NAMESPACE} ${SOURCE_POD}:${SOURCE_FILEPATH} ${TARGET_DIR}/${SOURCE_FILENAME}

CBF_EC_MOUNT_PATH ?= "./fpga-talon/bin"
CBF_BITSTREAM_RPD_SOURCE_DIR ?= /app/mnt/talondx-config/fpga-talon/bin
CBF_BITSTREAM_RPD_FILENAME ?= talon_dx-tdc_base-tdc_vcc_processing-application.hps.rpd
CBF_BITSTREAM_RPD_SOURCE_FILEPATH := ${CBF_BITSTREAM_RPD_SOURCE_DIR}/${CBF_BITSTREAM_RPD_FILENAME}
CBF_BITSTREAM_RPD_SOURCE_POD ?= ds-cbfcontroller-controller-0
CBF_BITSTREAM_RPD_SOURCE_POD_NAMESPACE ?= staging

copy-cbf-bitstream-rpd:
	@make k8s-file-copy \
		SOURCE_FILEPATH="${CBF_BITSTREAM_RPD_SOURCE_FILEPATH}" \
		SOURCE_FILENAME="${CBF_BITSTREAM_RPD_FILENAME}" \
		SOURCE_POD="${CBF_BITSTREAM_RPD_SOURCE_POD}" \
		TARGET_DIR="${CBF_EC_MOUNT_PATH}" \
		COPY_NAMESPACE="${CBF_BITSTREAM_RPD_SOURCE_POD_NAMESPACE}"