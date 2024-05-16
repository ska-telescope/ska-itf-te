set -eu
set -o pipefail

# log_by_selector finds all pods associated with a specified selector and downloads their logs.
# The pods and the downloaded logs' location are displayed.
#
# Environment Variables (REQUIRED):
#   selector: the Kubernetes selector used to find the pods.
#   namespace: the Kubernetes namespace within which to look for the pods.
log_by_selector () {
    value=${selector#*=}
    output_dir=sut-logs/${value}-logs/$(date +%Y%m%d-%H%M)
    mkdir -p ${output_dir}
    printf "%-40s | %-40s\n" "POD" "LOG_FILE"
    pods=$(kubectl get pods --namespace ${namespace} --selector ${selector} -o custom-columns=':metadata.name')
    for pod in ${pods}; do
        log_file=${output_dir}/${pod}.log
        kubectl logs --all-containers=true --namespace ${namespace} ${pod} > ${log_file}
        printf "%-40s | %-40s\n" ${pod} ${log_file}
    done
}
