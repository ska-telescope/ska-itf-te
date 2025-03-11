.PHONY: taranta-deploy-dish-tangogql taranta-check-env taranta-deploy-all-tangogql-instances

## TARGET: taranta-deploy-dish-tangogql
## SYNOPSIS: make taranta-deploy-dish-tangogql <target name>
## HOOKS: None
## VARS:
##       TANGO_HOST=<tangodb> - TangoDB FQDN
##
##  Create a TangoGQL deployment instance

taranta-deploy-dish-tangogql: TARANTA_PARAMS="--set tangogql.tangoDB=$(DISH_ID) --set global.tango_host=$(TANGO_DATABASE_DS).$(DISH_NAMESPACE).svc.$(CLUSTER_DOMAIN):10000 --set global.cluster_domain=$(CLUSTER_DOMAIN)"

taranta-deploy-dish-tangogql: taranta-check-env ## Deploy TangoGQL instance
	$(info Deployment Namespace: $(KUBE_NAMESPACE))
	$(info Dish Namespace: $(DISH_NAMESPACE))
	$(info Helm Release for base deployment: $(HELM_RELEASE))
	$(info Helm Release for this deployment: $(HELM_RELEASE)-$(DISH_ID))
	$(info Tango Host: $(TANGO_DATABASE_DS).$(DISH_NAMESPACE).svc.$(CLUSTER_DOMAIN):10000)
	$(info Setting Helm Chart Params: $(TARANTA_PARAMS))
	@make k8s-install-chart K8S_CHART=taranta-itf K8S_CHART_PARAMS=$(TARANTA_PARAMS) HELM_RELEASE=$(HELM_RELEASE)-$(DISH_ID)

LOWER_DISH_IDS=$(shell echo $(DISH_IDS) | tr A-Z a-z)
taranta-deploy-all-tangogql-instances:
	$(info DISH_IDS: $(LOWER_DISH_IDS))
	for ID in $(LOWER_DISH_IDS); do \
		if [[ ! -z "$(CI_COMMIT_TAG)" ]]; then \
			DISH_NAMESPACE=staging-dish-lmc-$$ID; \
		elif [[ "$(CI_PIPELINE_SOURCE)"=="merge_request_event" ]]; then \
			DISH_NAMESPACE=ci-dish-lmc-$$ID-$(CI_MERGE_REQUEST_SOURCE_BRANCH_NAME); \
		elif [[ "$(CI_COMMIT_BRANCH)" != "$(CI_DEFAULT_BRANCH)" ]]; then \
			DISH_NAMESPACE=ci-dish-lmc-$$ID-$(CI_COMMIT_BRANCH); \
		else \
			DISH_NAMESPACE=integration-dish-lmc-$$ID; \
		fi; \
		echo "##### Deploying TangoGQL for Dish $$ID... #####"; \
		make taranta-deploy-dish-tangogql DISH_ID=$$ID DISH_NAMESPACE=$$DISH_NAMESPACE; \
	done

taranta-check-env: ## Private target: Check environment configuration variables
ifndef TANGO_HOST
	$(error TANGO_HOST is undefined)
endif
ifndef CLUSTER_DOMAIN
	$(error CLUSTER_DOMAIN is undefined)
endif
