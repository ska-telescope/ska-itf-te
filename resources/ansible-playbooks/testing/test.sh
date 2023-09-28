#!/usr/bin/env bash

set -eux
set -o pipefail

# This script runs an ansible-playbook on a provided host.
# It takes 1 unnamed parameter:
# 1. MODE - this is the test mode to run: there are 3 options: 
#    1. default: runs the playbook with all options enabled.
#    2. gaia: runs the playbook as if it were executing on the gaia host.
#    3. raspberry_pi: runs the playbook as if it were executing on the raspberry_pi host.
#
# There are also the following environment variables which can be set:
# 1. TEST_HOST: the DNS or IP address of the host to test.
# 2. TEST_PORT: the port on which SSH is listening on the host. 


USER=ansible
MODE=${1}
TEST_PORT=${TEST_PORT:-22}
TEST_HOST=${TEST_HOST:-localhost}
base_dir="$(dirname "$(readlink -f "$0")")"

function cleanup_dir() {
    if [[ -n "${TEMP_DIR:-}" && -d "${TEMP_DIR:-}" ]]; then
        echo "Cleaning up tempdir ${TEMP_DIR}"
        rm -rf "${TEMP_DIR}"
    fi
}

function setup_tempdir() {
    TEMP_DIR=$(mktemp --directory "./${MODE}".XXXXXXXX)
    export TEMP_DIR
}

function setup_test_inventory() {
    export TEMP_INVENTORY_FILE="${TEMP_DIR}/hosts"
    cat > "${TEMP_INVENTORY_FILE}" << EOL
[raspberry_pi]
test_raspberry_pi ansible_host=${TEST_HOST} ansible_port=${TEST_PORT} host_identifier="Test Raspberry Pi"
[gaia]
test_gaia ansible_host=${TEST_HOST} ansible_port=${TEST_PORT} host_identifier="Test Gaia"
[test]
test_host ansible_host=${TEST_HOST} ansible_port=${TEST_PORT} host_identifier="Test Host"
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

function run_ansible_playbook() {
    case ${MODE} in
    raspberry_pi)
        NODE=raspberry_pi
        ;;
    gaia)
        NODE=gaia
        ;;
    default)
        NODE=test
        ;;
    *)
        echo "Invalid mode '${MODE}'."
        exit 1 
        ;;
    esac

    poetry run ansible-playbook --limit ${NODE} \
        -u=${USER} \
        -e @${base_dir}/../group_vars/atlas/atlas.yml \
        -v \
        -i ${TEMP_INVENTORY_FILE} \
        ${base_dir}/../site.yml
}

setup_tempdir
trap cleanup_dir EXIT
trap cleanup_dir ERR
setup_test_inventory
setup_ansible_cfg
run_ansible_playbook
