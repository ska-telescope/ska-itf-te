# run the dockerfile
docker run -it --env-file PrivateRules.mak registry.gitlab.com/ska-telescope/ska-mid-itf-engineering-tools/ska-mid-itf-engineering-tools:0.1.4

# git clone (to mimic the pipeline start)
mkdir /build && mkdir /build/ska-telescope && cd /build/ska-telescope 
git clone --recurse-submodules https://gitlab.com/ska-telescope/ska-mid-itf.git && cd ska-mid-itf
git checkout $CI_COMMIT_SHA -q && git show -q

#set up infra on the container (we might as well do this in the Dockerfile)
wget https://github.com/infrahq/infra/releases/download/v0.21.0/infra_0.21.0_amd64.deb
apt install ./infra_*.deb

# log into infra from the container
infra login https://boundary.skao.int --enable-ssh
infra use za-itf-k8s-master01-k8s

# Activate the virtual environment in the container if you want to run make lint
poetry shell

make python-format
make python-lint # add a few #noqas to get the thing going

# before executing the latest version install again
poetry install

# if you DON'T have the .venv running and you just ran poetry install, 
# use the following command but with `poetry run ` prepended
python3 -m src.ska_mid_itf_engineering_tools.talon_on

# prepended means
poetry run python3 -m src.ska_mid_itf_engineering_tools.talon_on

# WIP commands for testing
kubectl cp ${MCS_CONFIG_FILE_PATH}/hw_config.yaml ${KUBE_NAMESPACE}/ds-cbfcontroller-controller-0:/app/mnt/hw_config/hw_config.yaml