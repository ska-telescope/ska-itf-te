# All the old connection targets that we used to need are here.
# TODO: remove if no longer needed.
-include resources/itf-connect.mk

#Private targets and variables not to be checked in
-include PrivateRules.mak

#inlucde basic necessities for the Makefiles to work
include .make/base.mk

########################################################################
# PYTHON
########################################################################

include .make/python.mk

# https://github.com/pytest-dev/pytest-bdd/issues/401
PYTHON_VARS_BEFORE_PYTEST = PYTHONDONTWRITEBYTECODE=True

# better be verbose for debugging
PYTHON_VARS_AFTER_PYTEST ?= -v

PYTHON_TEST_FILE = tests/unit

python-post-lint:
	mypy --config-file mypy.ini src/ tests/

.PHONY: python-post-lint

########################################################################
# DOCS
########################################################################

include .make/docs.mk

DOCS_SPHINXOPTS = -n -W --keep-going

########################################################################
# OCI
########################################################################

include .make/oci.mk

########################################################################
# Helm
########################################################################

include .make/helm.mk

# only publish main chart not test parent
HELM_CHARTS_TO_PUBLISH=$(PROJECT_NAME)

########################################################################
# K8S
########################################################################

include .make/k8s.mk

DEPLOYMENT_CONTEXT ?= ITF-mid # TODO: Ask @Malte what this means.

# Chart for testing
ifeq ($(shell kubectl config current-context),minikube)
MINIKUBE ?= true
else
MINIKUBE ?= false
endif

ifneq ($(CI_JOB_ID),)
# For k8s-install-chart
_gitlab_image_tag = $(VERSION)-dev.c$(CI_COMMIT_SHORT_SHA)
_gitlab_registry = $(CI_REGISTRY_IMAGE)
else
# If we're running locally, use the most recent image from GitLab
_gitlab_image_tag = $(VERSION)-dev.c$(shell git rev-parse --short=8 @{u})
_gitlab_registry = registry.gitlab.com/$(shell git remote -v | head -1 | grep -oE 'ska-telescope(/[a-z0-9-]{1,}){1,}')
endif

K8S_CHART_PARAMS += \
	--set global.minikube=$(MINIKUBE) \
 	# --set ska-psi-low-subrack.image.registry=$(_gitlab_registry) \
 	# --set ska-psi-low-subrack.image.tag=$(_gitlab_image_tag)

# hack out PYTHONPATH - why is it even there? #TODO: Ask at CoP what the issue is here.
# hack in test target directory
K8S_TEST_TEST_COMMAND = unset PYTHONPATH; \
						$(PYTHON_VARS_BEFORE_PYTEST) pytest \
						$(PYTHON_VARS_AFTER_PYTEST) ./tests/functional \
						 | tee pytest.stdout ## k8s-test test command to run in container

ifeq ($(MAKECMDGOALS),k8s-test)
PYTHON_VARS_AFTER_PYTEST += \
    --cucumberjson=build/reports/cucumber.json \
	--json-report --json-report-file=build/reports/report.json

K8S_CHART_PARAMS += --set ska-taranta.enabled=false
endif

K8S_TEST_RUNNER_ADD_ARGS += --env=TANGO_HOST=$(shell helm get -n $(KUBE_NAMESPACE) values -a $(HELM_RELEASE) -o json | jq '.global.tango_host')

# PROXY_VALUES = \
# --env=http_proxy=${http_proxy} \
# --env=https_proxy=${http_proxy} \
# --env=no_proxy=${no_proxy}
