#!/bin/bash

set -eu
set -o pipefail

DS_SIM_NAMESPACE=${DS_SIM_NAMESPACE:-dish-structure-simulators}
DS_SIM_SERVICE=${DS_SIM_SERVICE:-ds-sim}

DS_SIM_HOST=$(kubectl -n ${DS_SIM_NAMESPACE} get svc ${DS_SIM_SERVICE} -o jsonpath={.status.loadBalancer.ingress[0].ip})
DS_SIM_HTTP_PORT=$(kubectl get svc -n ${DS_SIM_NAMESPACE} ${DS_SIM_SERVICE} -o jsonpath='{.spec.ports[?(@.name=="server")].port}')
DS_SIM_DISCOVER_PORT=$(kubectl get svc -n ${DS_SIM_NAMESPACE} ${DS_SIM_SERVICE} -o jsonpath='{.spec.ports[?(@.name=="discover")].port}')
DS_SIM_OPCUA_PORT=$(kubectl get svc -n ${DS_SIM_NAMESPACE} ${DS_SIM_SERVICE} -o jsonpath='{.spec.ports[?(@.name=="opcua")].port}')

cat << EOF
DS_SIM_HOST=${DS_SIM_HOST}
DS_SIM_HTTP_PORT=${DS_SIM_HTTP_PORT}
DS_SIM_DISCOVER_PORT=${DS_SIM_DISCOVER_PORT}
DS_SIM_OPCUA_PORT=${DS_SIM_OPCUA_PORT}
EOF
