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

example-start-server:
	uvicorn src.ska_cicd_training_pipeline_machinery.main:app --reload

PYTHON_VARS_AFTER_PYTEST= --disable-pytest-warnings

python-pre-lint:
	@echo "python-pre-lint: upgrade poetry for the time being."\
	python -V;\
	poetry --version;\
	poetry config virtualenvs.create false;\
	bash .make/resources/gitlab_section.sh poetryinstall "Install dependencies" poetry shell && poetry install --with dev;\
	poetry show;

python-pre-test:
	@echo "python-pre-test: running with: $(PYTHON_VARS_BEFORE_PYTEST) with $(PYTHON_RUNNER) pytest $(PYTHON_VARS_AFTER_PYTEST); \
    $(PYTHON_TEST_FILE)";\
	python -V;\
	bash .make/resources/gitlab_section.sh environment "Environment"  printenv;\
    echo "-----------------------";\
	poetry config virtualenvs.create false;\
	bash .make/resources/gitlab_section.sh upgrade_poetry "Upgrade Poetry" pip install --upgrade poetry;\
	bash .make/resources/gitlab_section.sh install_dependencies "Install dependencies" poetry install;\


# # All the old connection targets that we used to need are here.
# # TODO: remove if no longer needed.
-include resources/itf-connect.mk

### USEFUL BITS FROM LOW
# better be verbose for debugging
PYTHON_VARS_AFTER_PYTEST ?= -v

python-post-lint:
	mypy --config-file mypy.ini src/ tests/

.PHONY: python-post-lint

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
