#!/bin/bash

set -eux
set -o pipefail

MODE="$1"
base_dir="$(dirname "$(readlink -f "$0")")"

source ${base_dir}/vars.sh

REPO=ska-mid-itf
VERSION=1.0.0

function build() {
    docker build --tag ${CAR_OCI_REGISTRY_HOST}/${REPO}/${IMAGE}:${VERSION} \
    --file "${base_dir}/docker/${MODE}/Dockerfile" \
    "${base_dir}"
}

function push() {
    echo ${CAR_OCI_REGISTRY_PASSWORD} | docker login --username ${CAR_OCI_REGISTRY_USERNAME} --password-stdin ${CAR_OCI_REGISTRY_HOST} 
    docker push ${CAR_OCI_REGISTRY_HOST}/${REPO}/${IMAGE}:${VERSION}
}

build
push
