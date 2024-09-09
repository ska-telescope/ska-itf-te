PROJECT_ROOT ?= ../../	

## TARGET: itf-ds-sim-links
## SYNOPSIS: make itf-ds-sim-links
## HOOKS: none
## VARS: none
##  make target for generating the URLs for accessing the Dish Structure Simulator front-end
itf-ds-sim-links: export DS_SIM_NAMESPACE ?= $(KUBE_NAMESPACE)
itf-ds-sim-links: ## Create the URLs with which to access ds sim if it is available
	$(PROJECT_ROOT)/scripts/ds-sim/service-info.sh
.PHONY: itf-ds-sim-links

## TARGET: itf-ds-sim-env
## SYNOPSIS: make itf-ds-sim-env
## HOOKS: none
## VARS:
## 		BUILD_DIR=<directory in which to save the env vars>
## 		DS_SIM_NAMESPACE=<dish structure simulator namespace>
##
## make target for exporting dish structure simulator info as
## environment variables. Currently exports the following:
##   DS_SIM_HOST=<dish structure simulator IP address>
##	 DS_SIM_HTTP_PORT=<dish structure simulator web server port>
##   DS_SIM_DISCOVER_PORT=<dish structure simulator discover port>
##   DS_SIM_OPCUA_PORT=<<dish structure simulator OPCUA server port>
itf-ds-sim-env: BUILD_DIR ?= $(PROJECT_ROOT)/build/
itf-ds-sim-env: export DS_SIM_NAMESPACE ?= $(KUBE_NAMESPACE)
itf-ds-sim-env: ## Export ds sim connection details in .env file
	@echo $(DS_SIM_NAMESPACE)
	mkdir -p $(BUILD_DIR)
	$(PROJECT_ROOT)/scripts/ds-sim/service-env.sh | tee $(BUILD_DIR)/itf-ds-sim.env
.PHONY: itf-ds-sim-env

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

ODA_NAMESPACE=ska-db-oda
itf-install-oda:
	make k8s-install-chart K8S_CHART=ska-db-oda-mid-itf KUBE_APP=ska-db-oda KUBE_NAMESPACE=$(ODA_NAMESPACE)

itf-uninstall-oda:
	@make k8s-uninstall-chart K8S_CHART=ska-db-oda-mid-itf KUBE_APP=ska-db-oda KUBE_NAMESPACE=$(ODA_NAMESPACE)

# install taranta dashboards in separate namespace
k8s-install-taranta-dashboards:
#TODO: add target
	@make k8s-install-chart K8S_UMBRELLA_CHART_PATH=ska-tango-util KUBE_APP=tango-util KUBE_NAMESPACE=tango-util
	@make k8s-install-chart K8S_UMBRELLA_CHART_PATH=ska-tango-base KUBE_APP=tango-base KUBE_NAMESPACE=tango-base
	@make k8s-install-ska-tango-taranta-dashboard-pvc K8S_UMBRELLA_CHART_PATH=ska-tango-taranta-dashboard-pvc KUBE_APP=tango-base KUBE_NAMESPACE=tango-tar-pvc
#TODO: add target for skysimcontroller and other Test Equipment

sut-namespaces: ## Create both normal & SDP helmdeploy namespaces for SUT.
	@make k8s-namespace
	@make k8s-namespace KUBE_NAMESPACE=$(KUBE_NAMESPACE_SDP)

remove-sut-deployment:
	@make k8s-uninstall-chart || true
	@kubectl -n $(KUBE_NAMESPACE) delete pods,svc,daemonsets,deployments,replicasets,statefulsets,cronjobs,jobs,ingresses,configmaps --all --ignore-not-found
	@kubectl -n $(KUBE_NAMESPACE_SDP) delete pods,svc,daemonsets,deployments,replicasets,statefulsets,cronjobs,jobs,ingresses,configmaps --all --ignore-not-found
	@make k8s-delete-namespace || true
	@make k8s-delete-namespace KUBE_NAMESPACE=$(KUBE_NAMESPACE_SDP) || true

itf-cluster-credentials: sut-namespaces ## PIPELINE USE ONLY - allocate credentials for deployment namespaces
	curl -s https://gitlab.com/ska-telescope/templates-repository/-/raw/master/scripts/namespace_auth.sh | bash -s $(SERVICE_ACCOUNT) $(KUBE_NAMESPACE) $(KUBE_NAMESPACE_SDP) || true

links: itf-links

CLUSTER_DOMAIN_POSTFIX ?= miditf.internal.skao.int
KUBE_NAMESPACE_PREFIX ?= dish-lmc-
KUBE_NAMESPACE_POSTFIX ?=

## TARGET: itf-dish-ids
## SYNOPSIS: make itf-dish-ids
## HOOKS: none
## VARS: 
## 	  DISH_IDS=<Space separated string containing all Dish IDs to be connected to from TMC.>, default 
##    CLUSTER_DOMAIN_POSTFIX=<DishLMC Hosts' Cluster Domain postfixes>
##    TANGO_DATABASEDS=<TangoDB hostname>
##    KUBE_NAMESPACE_PREFIX=<Prefix for the Kubenamespaces for all the dishes>, default dish-lmc-
##    KUBE_NAMESPACE_POSTFIX?=<Postfix for the Kubenamespaces for all the dishes>, default None
##    SUT_CHART_DIR=Location of the SUT chart. Required: errors out if not set.
##  make target for generating the URLs for accessing the DishLMC deployments in the Mid ITF cluster

itf-dish-ids: ## Create the TMC values.yaml file needed to connect the Dishes to the TMC in the ITF
	@tmc_dish_ids
	@echo "Generated TMC values file: $(SUT_CHART_DIR)/tmc-values.yaml"
	@cat $(SUT_CHART_DIR)/tmc-values.yaml

## TARGET: itf-dish-links
## SYNOPSIS: make itf-dish-links
## HOOKS: none
## VARS: none
##  make target for generating the URLs for accessing the DishLMC deployments in the Mid ITF cluster

itf-dish-links: itf-links ## Create the URLs with which to access Taranta Dashboards

## TARGET: itf-links
## SYNOPSIS: make itf-links
## HOOKS: none
## VARS: KUBE_APP
##  make target for generating the URLs for accessing the Test Equipment deployment

itf-links: ## Create the URLs with which to access the Tango Control System if it is available
	@echo ${CI_JOB_NAME}
	@echo "##############################################################################################"
	@echo "#        Access the Taranta framework for the $(shell echo $(KUBE_APP) | tr a-z A-Z) Tango Control System here:"
	@echo "#        https://$(INGRESS_HOST)/$(KUBE_NAMESPACE)/taranta/devices"
	@echo "##############################################################################################"

CI_COMMIT_REF_NAME?=

DISH_ID?=

## TARGET: dpd-links
## SYNOPSIS: make dpd-links
## HOOKS: none
## VARS:
##   CI_JOB_NAME
##   KUBE_NAMESPACE
##   INGRESS_HOST
##  make target for generating the URLs for accessing the Data Product Dashboard in the Mid ITF.

dpd-links: ## Create the URLs with which to access the Data Product Dashboard
	@echo ${CI_JOB_NAME}
	@echo "##############################################################################################"
	@echo "#        Access the Data Product Dashboard here:"
	@echo "#        https://$(INGRESS_HOST)/$(KUBE_NAMESPACE)/dashboard/"
	@echo "##############################################################################################"

## TARGET: fix-pvc
## SYNOPSIS: make fix-pvc
## HOOKS: none
## VARS:
##   KUBE_NAMESPACE_SDP
##  make target for deploying the clone PVC whenever it inexplicably goes to the farm

fix-pvc: ## Create PVC in the SDP namespace for data product sharing
	kubectl apply -f charts/ska-mid-itf-dpd/templates/pvc.yaml -n ${KUBE_NAMESPACE_SDP}

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
	$(info K8S_TEST_RUNNER_PARAMS: $(K8S_TEST_RUNNER_PARAMS))
	$(info DPD_PVC_NAME: $(DPD_PVC_NAME))
	$(info DPD_PARAMS: $(DPD_PARAMS))
	$(info SDP_PARAMS: $(SDP_PARAMS))
	$(info ODA_PARAMS: $(ODA_PARAMS))
	$(info TMC_PARAMS: $(TMC_PARAMS))
	$(info SKA_TANGO_OPERATOR_DEPLOYED: $(SKA_TANGO_OPERATOR_DEPLOYED))
	$(info DISH_ID: $(DISH_ID))
	$(info HELM_RELEASE: $(HELM_RELEASE))
	$(info DISH_IDS: $(DISH_IDS))
	$(info CLUSTER_DOMAIN_POSTFIX: $(CLUSTER_DOMAIN_POSTFIX))
	$(info KUBE_NAMESPACE_PREFIX: $(KUBE_NAMESPACE_PREFIX))
	$(info KUBE_NAMESPACE_POSTFIX: $(KUBE_NAMESPACE_POSTFIX))
	$(info PYTHON_SRC: $(PYTHON_SRC))
	$(info DISH_LMC_IN_THE_LOOP: $(DISH_LMC_IN_THE_LOOP))
	$(info DISH_LMC_INITIAL_PARAMS: $(DISH_LMC_INITIAL_PARAMS))
	$(info DISH_LMC_EXTRA_PARAMS: $(DISH_LMC_EXTRA_PARAMS))
	$(info DISH_LMC_PARAMS: $(DISH_LMC_PARAMS))
	$(info Uppercase KUBE_APP: $(shell echo $(KUBE_APP) | tr a-z A-Z))
	$(info PROJECT_ROOT: $(PROJECT_ROOT))
	$(info DS_SIM_OPCUA_FQDN: $(DS_SIM_OPCUA_FQDN))
	$(info SPFRX_SIM_ENABLE: $(SPFRX_SIM_ENABLE))
	$(info SPFRX_IN_THE_LOOP: $(SPFRX_IN_THE_LOOP))
	$(info CBF_HW_IN_THE_LOOP: $(CBF_HW_IN_THE_LOOP))
	$(info SWITCH_CSP_ON: $(SWITCH_CSP_ON))
