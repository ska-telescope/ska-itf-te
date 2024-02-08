# Makefile targets for deploying and configuring the Talon HW
HW_CONFIG_FILE_PATH ?= $(PROJECT_ROOT)resources/talon
MCS_CONFIG_FILE_PATH ?= $(PROJECT_ROOT)resources/mcs
KUBE_NAMESPACE ?= $(KUBE_NAMESPACE)
LRU_INDEX ?= lru1
TALON_BOARD_IDX ?= 1

## TARGET: itf-cbf-talonlru-status
## SYNOPSIS: make itf-cbf-talonlru-status
## HOOKS: none
## VARS: 
##	HW_CONFIG_FILE_PATH=[scripts path] (default value: resources/talon)
##	LRU_INDEX=[lru index paramter] (default value: lru1)
##  make target for checking the Talon LRU status

itf-cbf-talonlru-status: ## Switch off the Talon LRU specified
	@[[ -f  $(HW_CONFIG_FILE_PATH)/talon_power_apc.sh ]] || exit 404;
	@cd $(HW_CONFIG_FILE_PATH) && ./talon_power_apc.sh $(LRU_INDEX)

## TARGET: itf-cbf-talonlru-off
## SYNOPSIS: make itf-cbf-talonlru-off
## HOOKS: none
## VARS: 
##	HW_CONFIG_FILE_PATH=[scripts path] (default value: resources/talon)
##	LRU_INDEX=[lru index paramter] (default value: lru1)
##  make target for switching off the Talon LRU

itf-cbf-talonlru-off: ## Switch off the Talon LRU specified
	@[[ -f  $(HW_CONFIG_FILE_PATH)/talon_power_apc.sh ]] || exit 404;
	@cd $(HW_CONFIG_FILE_PATH) && ./talon_power_apc.sh $(LRU_INDEX) off

## TARGET: itf-cbf-config-talon
## SYNOPSIS: make itf-cbf-config-talon
## HOOKS: none
## VARS: 
##	KUBE_NAMESPACE=[kubernetes namespace where MCS is deployed] (default value: integration)
##	TALON_BOARD_IDX=[Talon board index number] (default value: 1)
##  make target for configuring the Talon

itf-cbf-config-talon: ## generate talondx-config.json
	@kubectl exec -ti -n $(KUBE_NAMESPACE) ec-deployer -- python3 midcbf_deployer.py --generate-talondx-config --boards=$(TALON_BOARD_IDX)

## TARGET: itf-cbf-config-mcs
## SYNOPSIS: make itf-cbf-config-mcs
## HOOKS: none
## VARS:
##      MCS_CONFIG_FILE_PATH=[hw_config.yaml init_sys_param.json internal_params.json folder path] (default value: resources/mcs)
##      KUBE_NAMESPACE=[kubernetes namespace where MCS is deployed] (default value: integration)
##  make target for configuring the MCS

itf-cbf-config-mcs: ## Copy the Talon HW Config file onto a pod, copy the init sys params into the bite pod, copy the vcc gains json for band1 into the pod
	@kubectl -n $(KUBE_NAMESPACE) exec ec-bite -- /bin/bash -c "mkdir -p ext_config"
	@kubectl cp $(MCS_CONFIG_FILE_PATH)/hw_config.yaml $(KUBE_NAMESPACE)/ds-cbfcontroller-controller-0:/app/mnt/hw_config/hw_config.yaml
	@echo "Successfully copied Talon HW config file to the CBF Controller Pod."
	# @kubectl cp $(MCS_CONFIG_FILE_PATH)/init_sys_param.json  $(KUBE_NAMESPACE)/ec-bite:/app/images/ska-mid-cbf-engineering-console-bite/ext_config/initial_system_param.json
	# @echo "Successfully copied Initial System Parameters config file to the BITE pod for source data generation. Refer to "
	@kubectl cp $(MCS_CONFIG_FILE_PATH)/internal_params.json $(KUBE_NAMESPACE)/ds-vcc-vcc-001-0:/app/mnt/vcc_param/internal_params_receptor1_band1.json
	@echo "Successfully copied VCC gain parameters to the VCC device server pod."


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

## TARGET: itf-cbf-talon-on
## SYNOPSIS: make itf-cbf-talon-on
## HOOKS: none
## VARS: 
##	KUBE_NAMESPACE=[kubernetes namespace where MCS is deployed] (default value: integration)
##  CLUSTER_DOMAIN=[domain of the cluster where the MCS is running] (default value: miditf.internal.skao.int)
##  make target for switching on all the TalonDx' under control of the CSP.LMC

itf-cbf-talon-on:
	@export TANGO_HOST=tango-databaseds.$(KUBE_NAMESPACE).svc.$(CLUSTER_DOMAIN):10000 && \
	cd /app && poetry run python3 -m src.ska_mid_itf_engineering_tools.talon_on

## TARGET: itf-cbf-setup
## SYNOPSIS: make itf-cbf-setup
## HOOKS: none
## VARS: 
##	KUBE_NAMESPACE=[kubernetes namespace where MCS is deployed] (default value: integration)
##	HW_CONFIG_FILE_PATH=[scripts path] (default value: resources/talon)
##	LRU_INDEX=[lru index paramter] (default value: lru1)
##	TALON_BOARD_IDX=[Talon board index number] (default value: 1)
##  make target for registering the deviceservers in the TangoDB.


itf-cbf-setup: itf-cbf-talonlru-off itf-cbf-config-talon itf-cbf-config-mcs itf-cbf-tangocpp-update itf-cbf-config-tangodb
