#!/usr/bin/env bash

# This script creates a container and runs an ansible-playbook on it.
# It takes 2 unnamed parameters:
# 1. IMAGE - this the name of the image used to create the container.
# 2. MODE - this is the test mode to run: there are 3 options: 
#    1. default: runs the playbook with all options enabled.
#    2. gaia: runs the playbook as if it were executing on the gaia host.
#    3. raspberry_pi: runs the playbook as if it were executing on the raspberry_pi host.

set -eux
set -o pipefail

USER=ansible
IMAGE=${1}
MODE=${2}
CI_REGISTRY=${CI_REGISTRY:-registry.gitlab.com}
CI_PROJECT_NAMESPACE=${CI_PROJECT_NAMESPACE:-ska-telescope}
CI_PROJECT_NAME=${CI_PROJECT_NAME:-ska-mid-itf}
VERSION=${VERSION:-0.0.0}
IMAGE_FQDN=${CI_REGISTRY}/${CI_PROJECT_NAMESPACE}/${CI_PROJECT_NAME}/${IMAGE}:${VERSION}
identifier="$(< /dev/urandom tr -dc 'a-z0-9' | fold -w 5 | head -n 1)" ||:
NAME=${IMAGE}-${identifier}
base_dir="$(dirname "$(readlink -f "$0")")"

function cleanup_docker() {
    container_id=$(docker inspect --format="{{.Id}}" "${NAME}" ||:)
    if [[ -n "${container_id}" ]]; then
        echo "Cleaning up container ${NAME}"
        docker rm --force "${container_id}"
    fi
}

function start_container() {
    docker run -v /var/run/docker.sock:/var/run/docker.sock -d -P --name ${NAME} ${IMAGE_FQDN}
    export TEST_PORT=$(docker port ${NAME} 22/tcp | head -n1 | awk -F ':' '{print $2}')
}

start_container
trap cleanup_docker EXIT
trap cleanup_docker ERR
TEST_HOST=localhost
${base_dir}/test.sh ${MODE}

