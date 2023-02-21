k8s-install-spookd:
	make k8s-install-chart K8S_UMBRELLA_CHART_PATH=ska-mid-itf-spookd KUBE_APP=spookd KUBE_NAMESPACE=spookd

# install taranta application
k8s-install-taranta-application:
#TODO: add target

# install taranta dashboards in separate namespace
k8s-install-taranta-dashboards:
#TODO: add target

#TODO: Lots of targets missing for different things
