include ./resources/makefiles/test-equipment-dev.mk

## TARGET: itf-lmc-stage
## SYNOPSIS: make itf-lmc-stage
## HOOKS: none
## VARS: none
##  make target for installing DishLMC as they do it in ska-dish-lmc repository

itf-lmc-stage:
	helm repo add ska-helm-internal https://artefact.skao.int/repository/helm-internal
	helm upgrade --install dev ska-helm-internal/dish-lmc -n $(KUBE_NAMESPACE) \
		--set "global.dishes={001}" \
		--set "global.minikube=true" \
		--set "dishlmc.ska-mid-dish-manager.ska-mid-dish-simulators.enabled=true" \
		--set "dishlmc.ska-mid-dish-manager.ska-mid-dish-simulators.deviceServers.spfrxdevice.enabled=true" \
		--set "dishlmc.ska-mid-dish-manager.ska-mid-dish-simulators.deviceServers.spfdevice.enabled=true" \
		--set "dishlmc.ska-mid-dish-manager.ska-mid-dish-simulators.ska-tango-base.enabled=false" \
		--set "dishlmc.ska-mid-dish-ds-manager.ska-mid-dish-simulators.enabled=false" \
		--set "dishlmc.ska-mid-dish-ds-manager.ska-tango-base.enabled=false"

## TARGET: itf-te-install
## SYNOPSIS: make itf-te-install
## HOOKS: none
## VARS: none
##  make target for generating the URLs for accessing the Test Equipment deployment

itf-te-install:
	@make vars;
	@make k8s-install-chart

itf-te-template:
	@make vars;
	@make k8s-template-chart
	@mkdir -p build
	@mv manifests.yaml build/

	

## TARGET: itf-ds-links
## SYNOPSIS: make itf-ds-links
## HOOKS: none
## VARS: none
##  make target for generating the URLs for accessing the Dish Structure Simulator front-end

itf-ds-links: ## Create the URLs with which to access Skampi if it is available
	@echo ${CI_JOB_NAME}
	@echo "############################################################################"
	@echo "#            Access the Dish Structure Simulator Server here:"
	@echo "#            https://$(INGRESS_HOST)/$(KUBE_NAMESPACE)/novnc/"
	@echo "#			File uploads are easier here:"
	@echo "#            https://$(INGRESS_HOST)/$(KUBE_NAMESPACE)/fileserver/"
	@echo "############################################################################"

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

links: itf-te-links

## TARGET: itf-dish-links
## SYNOPSIS: make itf-dish-links
## HOOKS: none
## VARS: none
##  make target for generating the URLs for accessing the DishLMC deployments in the Mid ITF cluster

itf-dish-links: links ## Create the URLs with which to access Taranta Dashboards

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

## TARGET: itf-te-pass-env
## SYNOPSIS: make itf-te-pass-env
## HOOKS: none
## VARS: 
##	CI_COMMIT_REF_NAME=[branch-name] (default value: none)
##  make target for generating Gitlab CI configuration for SkySimCtl device server deployment

CI_COMMIT_REF_NAME?=

DISH_ID?=

itf-te-pass-env: KUBE_NAMESPACE := test-equipment
itf-te-pass-env: itf-skysimctl-links## Generate Gitlab CI configuration for SkySimCtl device server deployment

itf-skysimctl-links:
	@echo "KUBE_NAMESPACE=$(KUBE_NAMESPACE)"
	@mkdir -p build
	echo "TANGO_HOST=$(shell kubectl get -n $(KUBE_NAMESPACE) svc tango-databaseds -o jsonpath={'.status.loadBalancer.ingress[0].ip'}):10000" > build/deploy.env
	@echo "######################################################################"
	@echo "# THIS PIPELINE IS RUNNING FOR THE $(CI_COMMIT_REF_NAME) BRANCH"
	@echo "######################################################################"
	@if [[ -z "$(CI_COMMIT_REF_NAME)" ]]; then exit 1; fi
	@echo
	@echo "Exporting CI variables"
	@echo "UPSTREAM_CI_COMMIT_REF_NAME=$(CI_COMMIT_REF_NAME)" >> build/deploy.env # This is a workaround - see https://gitlab.com/gitlab-org/gitlab/-/issues/331596
	@echo "UPSTREAM_CI_JOB_ID=$(CI_JOB_ID)" >> build/deploy.env
	@cat build/deploy.env

# File browser vars
FILEBROWSER_ENV ?= dev
FILEBROWSER_CONFIG_SECRET_FILE := config.json
# This is overwritten in CI/CD
FILEBROWSER_CONFIG_PATH ?= ./charts/file-browser/secrets/example.json
FILEBROWSER_CONFIG_SECRET_NAME := file-browser-config-secret

## TARGET: file-browser-install
## SYNOPSIS: make file-browser-install
## HOOKS: none
## VARS:
##	FILEBROWSER_ENV=[environment-name] (default value: dev)
##	FILEBROWSER_CONFIG_SECRET_FILE=[name of file containing secrets (not path)] (default value: config.json)
##	FILEBROWSER_CONFIG_SECRET_NAME=[name of k8s secret created by file-browser-secrets] (default value: file-browser-config-secret)
##  make target for deploying the spectrum analyser file browser.

file-browser-install: K8S_CHART_PARAMS := $(K8S_CHART_PARAMS) --set mounts.configSecret.name=$(FILEBROWSER_CONFIG_SECRET_NAME) \
	--set mounts.configSecret.dest=$(FILEBROWSER_CONFIG_SECRET_FILE) \
	--set env.type=$(FILEBROWSER_ENV)
file-browser-install: K8S_CHART := file-browser
file-browser-install: KUBE_NAMESPACE := file-browser
file-browser-install: k8s-uninstall-chart file-browser-secrets k8s-install-chart

## TARGET: file-browser-secrets
## SYNOPSIS: make file-browser-secrets
## HOOKS: none
## VARS:
##	FILEBROWSER_CONFIG_PATH=[path to json config file with secrets. Overriden in CI/CD.] (default value: ../charts/file-browser/secrets/config.json)
##	FILEBROWSER_CONFIG_SECRET_FILE=[name of file containing secrets (not path).] (default value: config.json)
##	FILEBROWSER_CONFIG_SECRET_NAME=[name of k8s secret created by file-browser-secrets] (default value: file-browser-config-secret)
##  make target for creating k8s secret from JSON file located at $(FILEBROWSER_CONFIG_PATH)

file-browser-secrets: k8s-namespace
	kubectl delete secret -n $(KUBE_NAMESPACE) --ignore-not-found=true file-browser-config-secret
	kubectl create secret -n $(KUBE_NAMESPACE) generic $(FILEBROWSER_CONFIG_SECRET_NAME) --from-file=$(FILEBROWSER_CONFIG_SECRET_FILE)=$(FILEBROWSER_CONFIG_PATH)


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
	$(info TE_VERSION: $(TE_VERSION))
	$(info #####################################)
	$(info CLUSTER_DOMAIN: $(CLUSTER_DOMAIN))
	$(info #####################################)
	$(info MINIKUBE: $(MINIKUBE))
	$(info global.exposeAllDS=$(EXPOSE_All_DS))
	$(info global.tango_host=$(TANGO_HOST))
	$(info global.cluster_domain=$(CLUSTER_DOMAIN))
	$(info global.device_server_port=$(TANGO_SERVER_PORT))
	$(info global.operator=$(SKA_TANGO_OPERATOR))
	$(info ska-tango-base.display=$(DISPLAY))
	$(info ska-tango-base.xauthority=$(XAUTHORITY))
	$(info ska-tango-base.jive.enabled=$(JIVE))
	$(info ska-tango-base.itango.enabled=$(ITANGO_ENABLED))
	$(info TARANTA_PARAMS: $(TARANTA_PARAMS))
	$(info K8S_TEST_TANGO_IMAGE_PARAMS: ${K8S_TEST_TANGO_IMAGE_PARAMS})
	$(info SKIP_TANGO_EXAMPLES_PARAMS: ${SKIP_TANGO_EXAMPLES_PARAMS})
	$(info K8S_EXTRA_PARAMS: $(K8S_EXTRA_PARAMS))
	$(info K8S_CHARTS: $(K8S_CHARTS))
	$(info SKA_TANGO_OPERATOR_DEPLOYED: $(SKA_TANGO_OPERATOR_DEPLOYED))
	$(info DISH_ID: $(DISH_ID))
