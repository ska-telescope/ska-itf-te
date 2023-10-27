# Makefile targets for deploying and configuring the Talon HW
HW_CONFIG_FILE_PATH ?= $(PROJECT_ROOT)resources/talon
KUBE_NAMESPACE ?= $(KUBE_NAMESPACE)
LRU_INDEX ?= lru1
NUMBER_OF_TALON_BOARDS ?= 1

## TARGET: itf-cbf-talonlru-off
## SYNOPSIS: make itf-cbf-talonlru-off
## HOOKS: none
## VARS: 
##	HW_CONFIG_FILE_PATH=[scripts path] (default value: resources/talon)
##	LRU_INDEX=[lru index paramter] (default value: lru1)
##  make target for switching off the Talon LRU
COMMAND:=$(shell $(HW_CONFIG_FILE_PATH)/talon_power_apc.sh $(LRU_INDEX) off)

itf-cbf-talonlru-off: ## Switch off the Talon LRU specified
	@[[ -f  $(HW_CONFIG_FILE_PATH)/talon_power_apc.sh ]] || exit 404;
	@echo $(COMMAND)

## TARGET: itf-cbf-config-talon
## SYNOPSIS: make itf-cbf-config-talon
## HOOKS: none
## VARS: 
##	HW_CONFIG_FILE_PATH=[hw_config.yaml folder path] (default value: resources/talon)
##	KUBE_NAMESPACE=[kubernetes namespace where MCS is deployed] (default value: integration)
##	NUMBER_OF_TALON_BOARDS=[lru count paramter] (default value: 1)
##  make target for configuring the Talon

itf-cbf-config-talon: ## Copy the Talon HW Config file onto a pod and generate talondx-config.json
	@kubectl cp $(HW_CONFIG_FILE_PATH)/hw_config.yaml $(KUBE_NAMESPACE)/ds-cbfcontroller-controller-0:/app/mnt/hw_config/hw_config.yaml
	@kubectl exec -ti -n $(KUBE_NAMESPACE) ec-deployer -- python3 midcbf_deployer.py --generate-talondx-config --boards=$(NUMBER_OF_TALON_BOARDS)

## TARGET: itf-cbf-tangocpp-update
## SYNOPSIS: make itf-cbf-tangocpp-update
## HOOKS: none
## VARS: 
##	KUBE_NAMESPACE=[kubernetes namespace where MCS is deployed] (default value: integration)
##  make target for downloading all the CPP binaries from the CAR

itf-cbf-tangocpp-update: ## Download artefacts from CAR (Talon DeviceServer CPP binaries)
	@kubectl exec -ti -n $(KUBE_NAMESPACE) ec-deployer -- python3 midcbf_deployer.py --download-artifacts

## TARGET: itf-cbf-config-tangodb
## SYNOPSIS: make itf-cbf-tconfig-tangodb
## HOOKS: none
## VARS: 
##	KUBE_NAMESPACE=[kubernetes namespace where MCS is deployed] (default value: integration)
##  make target for registering the deviceservers in the TangoDB.

itf-cbf-config-tangodb: ## Configure Deviceservers in the TangoDB
	@kubectl exec -ti -n $(KUBE_NAMESPACE) ec-deployer -- python3 midcbf_deployer.py --config-db

## TARGET: itf-cbf-setup
## SYNOPSIS: make itf-cbf-setup
## HOOKS: none
## VARS: 
##	KUBE_NAMESPACE=[kubernetes namespace where MCS is deployed] (default value: integration)
##	HW_CONFIG_FILE_PATH=[scripts path] (default value: resources/talon)
##	LRU_INDEX=[lru index paramter] (default value: lru1)
##	NUMBER_OF_TALON_BOARDS=[lru count paramter] (default value: 1)
##  make target for registering the deviceservers in the TangoDB.

itf-cbf-setup: itf-cbf-talonlru-off itf-cbf-config-talon itf-cbf-tangocpp-update itf-cbf-config-tangodb
