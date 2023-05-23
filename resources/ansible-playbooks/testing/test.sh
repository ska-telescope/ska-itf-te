#!/usr/bin/env bash

set -eux
set -o pipefail

USER=ansible
NAME=${1}
MODE=${2}
CONTAINER_PORT=${CONTAINER_PORT:-22}
CONTAINER_HOST=${CONTAINER_HOST:-localhost}
base_dir="$(dirname "$(readlink -f "$0")")"

function cleanup_dir() {
    if [[ -n "${TEMP_DIR:-}" && -d "${TEMP_DIR:-}" ]]; then
        echo "Cleaning up tempdir ${TEMP_DIR}"
        rm -rf "${TEMP_DIR}"
    fi
}

function setup_tempdir() {
    TEMP_DIR=$(mktemp --directory "./${NAME}".XXXXXXXX)
    export TEMP_DIR
}

function setup_test_inventory() {
    export TEMP_INVENTORY_FILE="${TEMP_DIR}/hosts"
    cat > "${TEMP_INVENTORY_FILE}" << EOL
[raspberry_pi]
test_raspberry_pi ansible_host=${CONTAINER_HOST} ansible_port=${CONTAINER_PORT} host_identifier="Test Raspberry Pi"
[gaia]
test_gaia ansible_host=${CONTAINER_HOST} ansible_port=${CONTAINER_PORT} host_identifier="Test Gaia"
[test]
test_host ansible_host=${CONTAINER_HOST} ansible_port=${CONTAINER_PORT} host_identifier="Test Host"
EOL
}

function setup_ansible_cfg() {
    export ANSIBLE_CONFIG="${TEMP_DIR}/ansible.cfg"
    cat > "${ANSIBLE_CONFIG}" << EOL
[defaults]
# Avoid host key checking - to to run without interaction.
host_key_checking = False
EOL
}

function run_ansible_playbook_pi() {
    ansible-playbook -i ${TEMP_INVENTORY_FILE} --limit raspberry_pi \
	  ${base_dir}/../main.yml \
	  -u=${USER} \
      -v
}

function run_ansible_playbook_gaia() {
    ansible-playbook -i ${TEMP_INVENTORY_FILE} --limit gaia \
	  ${base_dir}/../main.yml \
	  -u=${USER} \
      -v
}

function run_ansible_playbook_test() {
    ansible-playbook -i ${TEMP_INVENTORY_FILE} --limit test \
	  ${base_dir}/../main.yml \
	  -u=${USER} \
      -v
}

setup_tempdir
trap cleanup_dir EXIT
trap cleanup_dir ERR
setup_test_inventory
setup_ansible_cfg

case ${MODE} in
raspberry_pi)
    run_ansible_playbook_pi
    ;;
gaia)
    run_ansible_playbook_gaia
    ;;
default)
    run_ansible_playbook_test
    ;;
*)
    echo "Invalid mode '${MODE}'."
    exit 1 
    ;;
esac

