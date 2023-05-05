ifeq ($(CI_JOB_NAME),deploy-test-equipment) # if CI_JOB_NAME is deploy-test-equipment
# Set K8S_EXTRA_PARAMS for deploying Test Equipment during development
TE_REGISTRY ?= registry.gitlab.com/ska-telescope/ska-ser-test-equipment
TE_IMAGE ?= ska-ser-test-equipment
TE_VERSION ?= 0.7.0

K8S_EXTRA_PARAMS = \
			--set test-equipment.image.registry=$(TE_REGISTRY) \
			--set test-equipment.image.image=$(TE_IMAGE) \
			--set test-equipment.image.tag=$(TE_VERSION) \
			--set test-equipment.image.pullPolicy=Always
endif

## TARGET: itf-te-install
## SYNOPSIS: make itf-te-install
## HOOKS: none
## VARS: none
##  make target for generating the URLs for accessing the Test Equipment deployment

itf-te-install:
	@make k8s-install-chart K8S_CHART=ska-mid-itf

itf-spookd-install:
	@make k8s-install-chart K8S_CHART=ska-mid-itf-ghosts KUBE_APP=spookd KUBE_NAMESPACE=$(SPOOKD_NAMESPACE) HELM_RELEASE=whoyougonnacall

SPOOKD_VALUES=charts/ska-mid-itf-ghosts/values.yaml
SPOOKD_VERSION=0.2.2
SPOOKD_NAMESPACE=spookd

itf-spookd-install-chart:
	helm install --values $(SPOOKD_VALUES) spookd-device-plugin skao/ska-ser-k8s-spookd --version $(SPOOKD_VERSION) --namespace spookd

itf-spookd-uninstall:
	@make k8s-uninstall-chart K8S_CHART=ska-mid-itf-ghosts KUBE_APP=spookd KUBE_NAMESPACE=$(SPOOKD_NAMESPACE) HELM_RELEASE=whoyougonnacall

itf-spookd-template-chart:
	@make k8s-template-chart K8S_CHART=ska-mid-itf-ghosts KUBE_APP=spookd KUBE_NAMESPACE=$(SPOOKD_NAMESPACE) HELM_RELEASE=whoyougonnacall

# install taranta dashboards in separate namespace
k8s-install-taranta-dashboards:
#TODO: add target
	@make k8s-install-chart K8S_UMBRELLA_CHART_PATH=ska-tango-util KUBE_APP=tango-util KUBE_NAMESPACE=tango-util
	@make k8s-install-chart K8S_UMBRELLA_CHART_PATH=ska-tango-base KUBE_APP=tango-base KUBE_NAMESPACE=tango-base
	@make k8s-install-ska-tango-taranta-dashboard-pvc K8S_UMBRELLA_CHART_PATH=ska-tango-taranta-dashboard-pvc KUBE_APP=tango-base KUBE_NAMESPACE=tango-tar-pvc
#TODO: add target for skysimcontroller and other Test Equipment

itf-cluster-credentials:  ## PIPELINE USE ONLY - allocate credentials for deployment namespaces
	make k8s-namespace
	make k8s-namespace KUBE_NAMESPACE=$(KUBE_NAMESPACE_SDP)
	curl -s https://gitlab.com/ska-telescope/templates-repository/-/raw/master/scripts/namespace_auth.sh | bash -s $(SERVICE_ACCOUNT) $(KUBE_NAMESPACE) $(KUBE_NAMESPACE_SDP) || true

## TARGET: itf-te-links
## SYNOPSIS: make itf-te-links
## HOOKS: none
## VARS: none
##  make target for generating the URLs for accessing the Test Equipment deployment

itf-te-links: ## Create the URLs with which to access Skampi if it is available
	@echo ${CI_JOB_NAME}
	@echo "############################################################################"
	@echo "#            Access the Test Equipment Taranta framework here:"
	@echo "#            https://$(INGRESS_HOST)/$(KUBE_NAMESPACE)/taranta/devices"
	@echo "############################################################################"
	@if [[ -z "${LOADBALANCER_IP}" ]]; then exit 0; \
	elif [[ $(shell curl -I -s -o /dev/null -I -w \'%{http_code}\' http$(S)://$(LOADBALANCER_IP)/$(KUBE_NAMESPACE)/taranta/devices) != '200' ]]; then \
		echo "ERROR: http://$(LOADBALANCER_IP)/$(KUBE_NAMESPACE)/taranta/devices unreachable"; exit 10; \
	fi

vars:
	$(info KUBE_NAMESPACE: $(KUBE_NAMESPACE))
	$(info #####################################)
	$(info TANGO_HOST: $(TANGO_HOST))
	$(info #####################################)
	$(info K8S_CHART_PARAMS: $(K8S_CHART_PARAMS))
	$(info #####################################)
	$(info VALUES: $(VALUES))
	$(info #####################################)
	$(info K8S_EXTRA_PARAMS: $(K8S_EXTRA_PARAMS))
	$(info #####################################)
