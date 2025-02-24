## TARGET: taranta-deploy-dish-tangogql
## SYNOPSIS: make taranta-deploy-dish-tangogql <target name>
## HOOKS: None
## VARS:
##       TANGO_HOST=<tangodb> - TangoDB FQDN
##
##  Create a TangoGQL deployment instance

taranta-deploy-dish-tangogql: TARANTA_PARAMS="--set tangogql.tangoDB=$(DISH_ID) --set global.tango_host=$(TANGO_DATABASE_DS).$(KUBE_NAMESPACE)-dish-lmc-$(DISH_ID).svc.$(CLUSTER_DOMAIN):10000 --set global.cluster_domain=$(CLUSTER_DOMAIN)"

taranta-deploy-dish-tangogql: taranta-check-env ## Deploy TangoGQL instance
	$(info Deploying one instance of TangoGQL in a namespace with one existing tangoGQL instance already running)
	$(info Namespace: $(KUBE_NAMESPACE))
	$(info Helm Release for base deployment: $(HELM_RELEASE))
	$(info Helm Release for this deployment: $(HELM_RELEASE)-$(DISH_ID))
	$(info Tango Host: $(TANGO_DATABASE_DS).$(KUBE_NAMESPACE)-dish-lmc-$(DISH_ID).svc.$(CLUSTER_DOMAIN):10000)
	$(info Setting Helm Chart Params: $(TARANTA_PARAMS))
	@bash .make/resources/gitlab_section.sh install-taranta "Installing TangoGQL for $(DISH_ID)" make k8s-install-chart K8S_CHART=taranta-itf K8S_CHART_PARAMS=$(TARANTA_PARAMS) HELM_RELEASE=$(HELM_RELEASE)-$(DISH_ID)

.PHONY: taranta-check-env

LOWER_DISH_IDS=$(shell echo $(DISH_IDS) | tr A-Z a-z)
taranta-deploy-all-tangogql-instances:
	$(info DISH_IDS: $(LOWER_DISH_IDS))
	for ID in $(LOWER_DISH_IDS); do \
	make taranta-deploy-dish-tangogql DISH_ID=$$ID; \
	done

taranta-check-env: ## Private target: Check environment configuration variables
ifndef TANGO_HOST
	$(error TANGO_HOST is undefined)
endif
ifndef CLUSTER_DOMAIN
	$(error CLUSTER_DOMAIN is undefined)
endif
