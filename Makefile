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

 python-pre-test:
	@echo "python-pre-test: running with: $(PYTHON_VARS_BEFORE_PYTEST) with $(PYTHON_RUNNER) pytest $(PYTHON_VARS_AFTER_PYTEST); \
    $(PYTHON_TEST_FILE)";\
    echo "Python Version:";\
    python -V;\
    echo "-----------------------";\
    echo "Environment variables:";\
    printenv;\
    echo "-----------------------"

# # All the old connection targets that we used to need are here.
# # TODO: remove if no longer needed.
-include resources/itf-connect.mk
