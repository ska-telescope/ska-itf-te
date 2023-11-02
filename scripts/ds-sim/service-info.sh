#!/bin/bash

DS_SIM_NAMESPACE=${DS_SIM_NAMESPACE:-dish-structure-simulators}
DS_SIM_SERVICE=${DS_SIM_SERVICE:-ds-sim}

DS_SIM_HOST=$(kubectl -n ${DS_SIM_NAMESPACE} get svc ${DS_SIM_SERVICE} -o jsonpath={.status.loadBalancer.ingress[0].ip})
SERVICE_PORTS=$(kubectl -n ${DS_SIM_NAMESPACE} get svc ${DS_SIM_SERVICE} -o jsonpath='{range @.spec.ports[*]}{@.name}{": "}{@.port}{";   "}{end}')

cat << EOF
${CI_JOB_NAME}
DS_SIM_NAMESPACE: ${DS_SIM_NAMESPACE}
DS_SIM_SERVICE: ${DS_SIM_SERVICE}
DS_SIM_HOST: ${DS_SIM_HOST}

############################################################################"
#            Access the Dish Structure Simulator web server here:"
#            http://${DS_SIM_HOST}:8090"
#            These are the available services and ports on ${DS_SIM_HOST}:"
#            ${SERVICE_PORTS}
############################################################################
EOF
