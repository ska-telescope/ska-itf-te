print-telescope-state:
	@poetry run telescope_state_control --print-state -n ${E2E_TEST_EXECUTION_NAMESPACE} -d "${DISH_IDS}"

teardown-telescope:
	@poetry run telescope_state_control --teardown -n ${E2E_TEST_EXECUTION_NAMESPACE} -d "${DISH_IDS}"

teardown-telescope-to-pre-assign:
	@poetry run telescope_state_control --teardown -n ${E2E_TEST_EXECUTION_NAMESPACE} -d "${DISH_IDS}" -c "ON" -b "STANDBY_FP"

CWD := $(shell pwd)
DISH_IDS ?= SKA001

test-e2e-kapb:
	infra use za-aa-k8s-master01-k8s
	kubectl delete job test-job -n integration-tests || true
	export KUBE_NAMESPACE=integration-tests; \
	export HELM_RELEASE=testing; \
	export K8S_UMBRELLA_CHART_PATH=$(CWD)/charts/ska-mid-testing; \
	export K8S_CHART=ska-mid-testing; \
	export K8S_CHART_PARAMS="--set environment.DISH_IDS=\"$(DISH_IDS)\""; \
	make k8s-template-chart > /dev/null
	@yq eval-all 'select(.kind == "Job" and .metadata.name == "test-job")' manifests.yaml > test-job.yaml
	kubectl apply -f test-job.yaml
	kubectl wait jobs -n integration-tests -l job-name=test-job --for=condition=complete --timeout="180s"
	@echo "Test job completed"
	@rm test-job.yaml manifests.yaml || true

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