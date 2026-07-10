#!/usr/bin/env bash
# Clones ska-mid-helmreleases, extracts the ska-mid chart version pinned on
# the main branch, prints it to stdout, and cleans up the clone.
#
# Auth is attempted in this order:
#   1. CI_JOB_TOKEN     - standard GitLab CI token (same GitLab instance,
#                         requires ska-mid-helmreleases to allow this project
#                         in Settings > CI/CD > Token Access)
#   2. HELMRELEASES_ACCESS_TOKEN - a project/group access token with read_repository
#                         scope, stored as a masked CI variable on this project
#   3. No auth          - fallback for public repos
set -euo pipefail

REPO_PATH="ska-telescope/ska-mid-helmreleases"
GITLAB_HOST="gitlab.com"
HELMRELEASE_FILE="ska-mid-helmreleases/datacentres/shared/deployment/central-controller/helmrelease.yml"

if [ -n "${CI_JOB_TOKEN:-}" ]; then
    CLONE_URL="https://gitlab-ci-token:${CI_JOB_TOKEN}@${GITLAB_HOST}/${REPO_PATH}.git"
elif [ -n "${HELMRELEASES_ACCESS_TOKEN:-}" ]; then
    CLONE_URL="https://oauth2:${HELMRELEASES_ACCESS_TOKEN}@${GITLAB_HOST}/${REPO_PATH}.git"
else
    CLONE_URL="https://${GITLAB_HOST}/${REPO_PATH}.git"
fi

git clone --branch main --depth 1 "${CLONE_URL}" ska-mid-helmreleases >&2

VERSION=$(grep 'version:' "${HELMRELEASE_FILE}" | sed 's/.*version: *//;s/"//g;s/ //g')

rm -rf ska-mid-helmreleases

echo "${VERSION}"
