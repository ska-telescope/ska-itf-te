print-telescope-state:
	@poetry run telescope_state_control --print-state -n ${E2E_TEST_EXECUTION_NAMESPACE} -d "${DISH_IDS}"

teardown-telescope:
	@poetry run telescope_state_control --teardown -n ${E2E_TEST_EXECUTION_NAMESPACE} -d "${DISH_IDS}"

teardown-telescope-to-pre-assign:
	@poetry run telescope_state_control --teardown -n ${E2E_TEST_EXECUTION_NAMESPACE} -d "${DISH_IDS}" -c "ON" -b "STANDBY_FP"

CWD := $(shell pwd)

define RENDER_AND_EXECUTE_TEST_JOB
	@read -p "Testing against production. Context will be switched to za-aa-k8s-master01-k8s. Continue? (Y/n): " confirm; [ "$$confirm" = Y ] || { echo "Aborted."; exit 1; }
	@infra use za-aa-k8s-master01-k8s
	kubectl delete job $(1) -n integration-tests || true
	@export KUBE_NAMESPACE=integration-tests; \
	export HELM_RELEASE=testing; \
	export K8S_UMBRELLA_CHART_PATH=$(CWD)/charts/ska-mid-testing; \
	export K8S_CHART=ska-mid-testing; \
	make k8s-template-chart > /dev/null
	@yq eval-all "select(.kind == \"Job\" and .metadata.name == \"$(1)-job\" and .spec.template.spec.containers[].name == \"$(1)\")" manifests.yaml > $(1)-job.yaml
	kubectl apply -f $(1)-job.yaml
	kubectl wait jobs -n integration-tests -l job-name=$(1) --for=condition=complete --timeout="180s"	
	@echo "Test completed"
	@rm manifests.yaml || true
endef

test-custom-kapb:
	$(eval TEST_NAME := custom-test)
	@yq -i '.testJobName = "$(TEST_NAME)"' $(CWD)/charts/ska-mid-testing/values.yaml
	$(call RENDER_AND_EXECUTE_TEST_JOB,custom-test)

## TARGET: test-smoke-kapb
## SYNOPSIS: make test-smoke-kapb
## HOOKS: none
## VARS:
##   None
##  make target for running a smoke test using a kubernetes job in the Losberg cluster

test-smoke-kapb: ## Run smoke test k8s job in Losberg cluster
	$(call RENDER_AND_EXECUTE_TEST_JOB,smoke-test)

## TARGET: test-e2e-kapb
## SYNOPSIS: make test-e2e-kapb
## HOOKS: none
## VARS:
##   TEST_NAME
##  make target for running an end-to-end test using a kubernetes job in the Losberg cluster

test-e2e-kapb: ## Run end-to-end test job in the Losberg cluster
	$(eval TEST_NAME := end-to-end-test)
	@yq -i '.E2ETest = "tests/integration/tmc/test_scan.py::test_perform_a_scan_via_tmc"' $(CWD)/charts/ska-mid-testing/values.yaml
	@yq -i '.testJobName = "$(TEST_NAME)"' $(CWD)/charts/ska-mid-testing/values.yaml
	$(call RENDER_AND_EXECUTE_TEST_JOB,$(TEST_NAME))

test-telescope-on-kapb: ## Run Telescope On command using a k8s test job executed in the Losberg cluster.
	$(eval TEST_NAME := telescope-on-test)
	@yq -i '.E2ETest = "tests/integration/tmc/test_telescope_on.py::test_telescope_on_via_tmc"' $(CWD)/charts/ska-mid-testing/values.yaml
	@yq -i '.testJobName = "$(TEST_NAME)"' $(CWD)/charts/ska-mid-testing/values.yaml
	$(call RENDER_AND_EXECUTE_TEST_JOB,$(TEST_NAME))

test-assign-resources-kapb:
	$(eval TEST_NAME := assign-resources-test)
	@yq -i '.E2ETest = "tests/integration/tmc/test_individual_commands.py::test_assign_resources_via_tmc"' $(CWD)/charts/ska-mid-testing/values.yaml
	@yq -i '.testJobName = "$(TEST_NAME)"' $(CWD)/charts/ska-mid-testing/values.yaml
	$(call RENDER_AND_EXECUTE_TEST_JOB,$(TEST_NAME))

test-configure-scan-kapb:
	$(eval TEST_NAME := configure-scan-test)
	@yq -i '.E2ETest = "tests/integration/tmc/test_individual_commands.py::test_configure_scan_via_tmc"' $(CWD)/charts/ska-mid-testing/values.yaml
	@yq -i '.testJobName = "$(TEST_NAME)"' $(CWD)/charts/ska-mid-testing/values.yaml
	$(call RENDER_AND_EXECUTE_TEST_JOB,$(TEST_NAME))

test-scan-kapb:
	$(eval TEST_NAME := scan-test)
	@yq -i '.E2ETest = "tests/integration/tmc/test_individual_commands.py::test_scan_via_tmc"' $(CWD)/charts/ska-mid-testing/values.yaml
	@yq -i '.testJobName = "$(TEST_NAME)"' $(CWD)/charts/ska-mid-testing/values.yaml
	$(call RENDER_AND_EXECUTE_TEST_JOB,$(TEST_NAME))

test-end-observation-kapb:
	$(eval TEST_NAME := end-observation-test)
	@yq -i '.E2ETest = "tests/integration/tmc/test_individual_commands.py::test_end_observation_via_tmc"' $(CWD)/charts/ska-mid-testing/values.yaml
	@yq -i '.testJobName = "$(TEST_NAME)"' $(CWD)/charts/ska-mid-testing/values.yaml
	$(call RENDER_AND_EXECUTE_TEST_JOB,$(TEST_NAME))

test-release-resources-kapb:
	$(eval TEST_NAME := release-resources-test)
	@yq -i '.E2ETest = "tests/integration/tmc/test_individual_commands.py::test_release_resources_via_tmc"' $(CWD)/charts/ska-mid-testing/values.yaml
	@yq -i '.testJobName = "$(TEST_NAME)"' $(CWD)/charts/ska-mid-testing/values.yaml
	$(call RENDER_AND_EXECUTE_TEST_JOB,$(TEST_NAME))

make-version:
	echo $(MAKE_VERSION)

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