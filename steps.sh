#############################################################################################################################
# This file contains a few nice commands to generate a local environment as close as possible to that of the Gitlab Runner. #
#############################################################################################################################

# run the dockerfile
IMAGE=registry.gitlab.com/ska-telescope/ska-mid-itf-engineering-tools/ska-mid-itf-engineering-tools
IMAGE_VERSION=0.9.2-dev.c0ef99b9c
# IMAGE_VERSION=0.9.1
docker run -it -e CI_COMMIT_SHA=$(git rev-parse --short HEAD) --env-file PrivateRules.mak $IMAGE:$IMAGE_VERSION

# git clone (to mimic the pipeline start)
mkdir /build && mkdir /build/ska-telescope && cd /build/ska-telescope 
git clone --recurse-submodules https://gitlab.com/ska-telescope/ska-mid-itf.git && cd ska-mid-itf
git checkout $CI_COMMIT_SHA -q && git show -q

# log into infra from the container
# infra login https://boundary.skao.int --enable-ssh
# infra use za-itf-k8s-master01-k8s

# IF PYTHONPATH FIX WORKS, DELETE THIS:
# # Activate the virtual environment in the container if you want to run make lint
# poetry shell

# BEFORE poetry shell:
root@30ce45f0f0aa:/build/ska-telescope/ska-mid-itf# env | grep PATH
PYTHONPATH=/app/src:/app/src:/app/.venv/lib/python3.10/site-packages
PATH=/app/.venv/bin:/app/bin:/app/.venv/bin:/app/.local/bin:/app/bin:/app/.local/bin:/app/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# AFTER poetry shell:
(ska-mid-itf-py3.10) root@30ce45f0f0aa:/build/ska-telescope/ska-mid-itf# env | grep PATH
PYTHONPATH=/app/src:/app/src:/app/.venv/lib/python3.10/site-packages
PATH=/build/ska-telescope/ska-mid-itf/.venv/bin:/app/.venv/bin:/app/bin:/app/.venv/bin:/app/.local/bin:/app/bin:/app/.local/bin:/app/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# INSTEAD OF poetry shell, run:

# Once the shell is active, install everything
poetry install && export PATH=/build/ska-telescope/ska-mid-itf/.venv/bin:${PATH}

make python-format
make python-lint # add a few #noqas to get the thing going

# before executing the latest version install again
poetry install

# run talon_on like the Gitlab Runner:
talon_on

# if you DON'T have the .venv running and you just ran poetry install, 
# use the following command but with `poetry run ` prepended
python3 -m src.ska_mid_itf_engineering_tools.talon_on

# prepended means
poetry run python3 -m src.ska_mid_itf_engineering_tools.talon_on

# WIP commands for testing
kubectl cp ${MCS_CONFIG_FILE_PATH}/hw_config.yaml ${KUBE_NAMESPACE}/ds-cbfcontroller-controller-0:/app/mnt/hw_config/hw_config.yaml

# Gitlab steps for local container execution
make k8s-install-chart
make k8s-wait
make itf-cbf-talonlru-off && sleep 3
# make itf-cbf-config-talon && sleep 3
make itf-cbf-config-mcs && sleep 3
# make itf-cbf-tangocpp-update &> deploy/talonconfig.log && sleep 3
# make itf-cbf-config-tangodb && sleep 3
make itf-cbf-tango-on || cat /app/src/ska_mid_itf_engineering_tools/cbf_config/talon_on.py && make itf-cbf-power-on && echo "###############\n# Failed to deploy Talon Demonstrator Correlator\n###############" > deploy/status

# Run integration test
export TANGO_DATABASE_DS=tango-databaseds
export KUBE_NAMESPACE=integration
export CLUSTER_DOMAIN=miditf.internal.skao.int
make integration-test TANGO_HOST=$TANGO_DATABASE_DS.$KUBE_NAMESPACE.svc.$CLUSTER_DOMAIN:10000