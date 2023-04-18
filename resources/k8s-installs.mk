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

vars:
	$(info KUBE_NAMESPACE: $(KUBE_NAMESPACE))
	$(info TANGO_HOST: $(TANGO_HOST))
	$(info K8S_CHART_PARAMS: $(K8S_CHART_PARAMS))
	$(info VALUES: $(VALUES))
