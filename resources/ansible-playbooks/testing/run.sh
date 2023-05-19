#!/usr/bin/env bash

set -euo pipefail

USER=p.jordaan
MODE="$1"
identifier="$(< /dev/urandom tr -dc 'a-z0-9' | fold -w 5 | head -n 1)" ||:
NAME="ansible-test-node-${identifier}"
base_dir="$(dirname "$(readlink -f "$0")")"

function cleanup() {
    container_id=$(docker inspect --format="{{.Id}}" "${NAME}" ||:)
    if [[ -n "${container_id}" ]]; then
        echo "Cleaning up container ${NAME}"
        docker rm --force "${container_id}"
    fi
    if [[ -n "${TEMP_DIR:-}" && -d "${TEMP_DIR:-}" ]]; then
        echo "Cleaning up tempdir ${TEMP_DIR}"
        rm -rf "${TEMP_DIR}"
    fi
}

function setup_tempdir() {
    TEMP_DIR=$(mktemp --directory "/tmp/${NAME}".XXXXXXXX)
    export TEMP_DIR
}

function create_temporary_ssh_id() {
    ssh-keygen -b 2048 -t rsa -C "${USER}@test.com" -f "${TEMP_DIR}/id_rsa" -N ""
    chmod 600 "${TEMP_DIR}/id_rsa"
    chmod 644 "${TEMP_DIR}/id_rsa.pub"
}

function start_container() {
    docker build --tag "ansible-test-node" \
        --build-arg USER \
        --file "${base_dir}/docker/${MODE}/Dockerfile" \
        "${TEMP_DIR}"
    docker run -d -P --name "${NAME}" "ansible-test-node"
    CONTAINER_PORT=$(docker port ${NAME} 22/tcp | head -n1 | awk -F ':' '{print $2}')
    export CONTAINER_ADDR
}

function setup_test_inventory() {
    export TEMP_INVENTORY_FILE="${TEMP_DIR}/hosts"
    cat > "${TEMP_INVENTORY_FILE}" << EOL
[raspberry_pi]
test_raspberry_pi ansible_host=localhost ansible_port=${CONTAINER_PORT} host_identifier="Test Raspberry Pi"
[gaia]
test_gaia ansible_host=localhost ansible_port=${CONTAINER_PORT} host_identifier="Test Gaia" ansible_ssh_pass=p.jordaan ansible_become_pass=p.jordaan
[test]
test_host ansible_host=localhost ansible_port=${CONTAINER_PORT} host_identifier="Test Host"
[all:vars]
ansible_ssh_private_key_file=${TEMP_DIR}/id_rsa
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
trap cleanup EXIT
trap cleanup ERR
create_temporary_ssh_id
start_container
setup_test_inventory
setup_ansible_cfg

case ${MODE} in
raspberry_pi)
    run_ansible_playbook_pi
    ;;
gaia)
    run_ansible_playbook_gaia
    ;;
test)
    run_ansible_playbook_test
    ;;
*)
    echo "Invalid mode '${MODE}'."
    exit 1 
    ;;
esac

