
## TARGET: tmc-logs
## SYNOPSIS: make tmc-logs KUBE_NAMESPACE=integration
## HOOKS: none
## VARS:
##	KUBE_NAMESPACE=[Namespace in which to look for TMC logs]
##  make target for downloading all TMC logs in a given namespace.
##  logs are placed in sut-logs/ska-tmc-mid-logs/$date
tmc-logs:
	@scripts/kubernetes/log_subsystem.sh ska-tmc-mid ${KUBE_NAMESPACE}
.PHONY: tmc-logs

## TARGET: cbf-logs
## SYNOPSIS: make cbf-logs KUBE_NAMESPACE=integration
## HOOKS: none
## VARS:
##	KUBE_NAMESPACE=[Namespace in which to look for CBF logs]
##  make target for downloading all CBF logs in a given namespace.
##  logs are placed in sut-logs/cbfmcs-mid-logs/$date
cbf-logs:
	@scripts/kubernetes/log_subsystem.sh cbfmcs-mid ${KUBE_NAMESPACE}
.PHONY: cbf-logs

## TARGET: csp-logs
## SYNOPSIS: make csp-logs KUBE_NAMESPACE=integration
## HOOKS: none
## VARS:
##	KUBE_NAMESPACE=[Namespace in which to look for CSP logs]
##  make target for downloading all CSP logs in a given namespace.
##  logs are placed in sut-logs/csp-lmc-logs/$date
csp-logs:
	@scripts/kubernetes/log_subsystem.sh csp-lmc ${KUBE_NAMESPACE}
.PHONY: csp-logs


## TARGET: sdp-logs
## SYNOPSIS: make sdp-logs KUBE_NAMESPACE=integration
## HOOKS: none
## VARS:
##	KUBE_NAMESPACE=[Namespace in which to look for SDP logs]
##  make target for downloading all SDP logs in a given namespace.
##  logs are placed in sut-logs/sdp-logs/$date
sdp-logs:
	@scripts/kubernetes/log_system.sh sdp ${KUBE_NAMESPACE}
.PHONY: sdp-logs


## TARGET: vis-receive-logs
## SYNOPSIS: make vis-receive-logs KUBE_NAMESPACE_SDP=integration-sdp
## HOOKS: none
## VARS:
##	KUBE_NAMESPACE_SDP=[Namespace in which to look for SDP logs]
##  make target for downloading all SDP vis-receive pod logs in a given namespace.
##  logs are placed in sut-logs/vis-receive-logs/$date
vis-receive-logs:
	@scripts/kubernetes/log_script.sh vis-receive ${KUBE_NAMESPACE_SDP}
.PHONY: vis-receive-logs

## TARGET: dish-logs
## SYNOPSIS: make dish-logs KUBE_NAMESPACE=integration
## HOOKS: none
## VARS:
##	KUBE_NAMESPACE=[Namespace in which to look for Dish LMC logs]
##  make target for downloading all Dish LMC logs in a given namespace.
##  logs are placed in sut-logs/ska-dish-lmc-logs/$date
dish-logs:
	@scripts/kubernetes/log_subsystem.sh ska-dish-lmc ${KUBE_NAMESPACE}
.PHONY: dish-logs
