#########################################################################
# WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING 
#########################################################################
# This Makefile was copied from the Low ITF repository and caused a world
# of pain. Don't just use.
PROJECT = ska-ser-test-equipment

# only publish main chart not test umbrella
HELM_CHARTS_TO_PUBLISH=$(PROJECT)

# Chart for testing
MINIKUBE ?= true
VALUES ?=
TANGO_HOST ?= tango-databaseds:10000  ## TANGO_HOST needed for k8s-test

#### PYTHON CUSTOM VARS
DOCS_SPHINXOPTS=-n -W --keep-going

# Use the previously built image when running in the pipeline
ifneq ($(CI_JOB_ID),)
OCI_TAG = $(VERSION)-dev.c$(CI_COMMIT_SHORT_SHA)
CI_REGISTRY ?= registry.gitlab.com
# For k8s-install-chart
VALUES += --set test_equipment.image.registry=$(CI_REGISTRY)/ska-telescope/$(NAME) \
	--set test_equipment.image.tag=$(OCI_TAG)
# for k8s-test
K8S_TEST_IMAGE_TO_TEST=$(CI_REGISTRY)/ska-telescope/$(NAME)/$(NAME):$(OCI_TAG)
endif

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

K8S_CHART = test-parent
K8S_CHART_PARAMS = --set global.tango_host=$(TANGO_HOST) --set global.minikube=$(MINIKUBE) $(VALUES)

-include PrivateRules.mak

include .make/base.mk

include .make/python.mk

include .make/oci.mk

include .make/helm.mk

include .make/k8s.mk

python-post-format:
	docformatter -r -i --pre-summary-newline src/ tests/

python-post-lint:
	mypy --config-file mypy.ini src/ tests/

### PYTHON END

k8s-reinstall-chart: k8s-uninstall-chart k8s-install-chart

.PHONY: python-post-format python-post-lint
