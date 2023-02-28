k8s-install-spookd:
	@make k8s-install-chart K8S_UMBRELLA_CHART_PATH=ska-mid-itf-spookd KUBE_APP=spookd KUBE_NAMESPACE=spookd

# install taranta dashboards in separate namespace
k8s-install-taranta-dashboards:
#TODO: add target
	@make k8s-install-chart K8S_UMBRELLA_CHART_PATH=ska-tango-util KUBE_APP=tango-util KUBE_NAMESPACE=tango-util
	@make k8s-install-chart K8S_UMBRELLA_CHART_PATH=ska-tango-base KUBE_APP=tango-base KUBE_NAMESPACE=tango-base
	@make k8s-install-ska-tango-taranta-dashboard-pvc K8S_UMBRELLA_CHART_PATH=ska-tango-taranta-dashboard-pvc KUBE_APP=tango-base KUBE_NAMESPACE=tango-tar-pvc
#TODO: add target for skysimcontroller and other Test Equipment

