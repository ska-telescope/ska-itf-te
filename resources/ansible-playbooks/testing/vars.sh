#!/usr/bin/env bash

CAR_OCI_REGISTRY_HOST="${CAR_OCI_REGISTRY_HOST:-artefact.skao.int}"
IMAGE_PREFIX=ansible-testing-image
IMAGE=${IMAGE_PREFIX}-${MODE}
REPO=ska-mid-itf
VERSION=1.0.0
IMAGE_FQDN=${CAR_OCI_REGISTRY_HOST}/${REPO}/${IMAGE}:${VERSION}
