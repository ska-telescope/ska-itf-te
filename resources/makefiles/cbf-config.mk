# Makefile targets for deploying and configuring the Talon HW
HW_CONFIG_FILE_PATH ?= $(PROJECT_ROOT)resources/talon
MCS_CONFIG_FILE_PATH ?= $(PROJECT_ROOT)resources/mcs
SLIM_CONFIG_FILE_PATH ?= $(PROJECT_ROOT)resources/mcs
KUBE_NAMESPACE ?= $(KUBE_NAMESPACE)
TALON_BOARD_IDX ?= "1,2,3,4" #Set the index of all the boards that should be deployed.

## TARGET: itf-cbf-talonlru-status
## SYNOPSIS: make itf-cbf-talonlru-status
## HOOKS: none
## VARS: 
##	HW_CONFIG_FILE_PATH=[scripts path] (default value: resources/talon)
##  make target for checking the Talon LRU status

itf-cbf-talonlru-status: ## Specified Talon LRU status
	@[[ -f  $(HW_CONFIG_FILE_PATH)/talon_power_apc.sh ]] || exit 404;
	@cd $(HW_CONFIG_FILE_PATH) && \
	./talon_power_apc.sh lru1 && \
	./talon_power_apc.sh lru2

## TARGET: itf-cbf-talonlru-off
## SYNOPSIS: make itf-cbf-talonlru-off
## HOOKS: none
## VARS: 
##	HW_CONFIG_FILE_PATH=[scripts path] (default value: resources/talon)
##  make target for switching off the Talon LRU

itf-cbf-talonlru-off: ## Switch off the Talon LRU specified
	@[[ -f  $(HW_CONFIG_FILE_PATH)/talon_power_apc.sh ]] || exit 404;
	@cd $(HW_CONFIG_FILE_PATH) && \
	./talon_power_apc.sh lru1 off && \
	./talon_power_apc.sh lru2 off

## TARGET: itf-cbf-config-mcs
## SYNOPSIS: make itf-cbf-config-mcs
## HOOKS: none
## VARS:
##      MCS_CONFIG_FILE_PATH=[hw_config.yaml init_sys_param.json internal_params.json folder path] (default value: resources/mcs)
##      KUBE_NAMESPACE=[kubernetes namespace where MCS is deployed] (default value: integration)
##  make target for configuring the MCS

itf-cbf-config-mcs: itf-cbf-copy-slim-config itf-cbf-copy-hw-config ## Copy the init sys params into the bite pod, copy the vcc gains json for band1 into the pod
	@kubectl cp $(MCS_CONFIG_FILE_PATH)/internal_params.json $(KUBE_NAMESPACE)/ds-vcc-vcc-001-0:/app/mnt/vcc_param/internal_params_receptor1_band1.json
	@echo "Successfully copied VCC gain parameters to the VCC device server pod."

## TARGET: itf-cbf-copy-slim-config
## SYNOPSIS: make itf-cbf-copy-config
## HOOKS: none
## VARS:
##      MCS_CONFIG_FILE_PATH=[hw_config.yaml init_sys_param.json internal_params.json fs_slim_config.yaml vis_slim_config.yaml folder path] (default value: resources/mcs)
##      KUBE_NAMESPACE=[kubernetes namespace where MCS is deployed] (default value: integration)
##  make target for configuring the MCS - specifically HW config

itf-cbf-copy-slim-config: ## Copy the Talon HW Config file onto a pod
	@kubectl cp $(SLIM_CONFIG_FILE_PATH)/fs_slim_config.yaml $(KUBE_NAMESPACE)/ds-cbfcontroller-controller-0:/app/mnt/slim/fs_slim_config.yaml
	@kubectl cp $(SLIM_CONFIG_FILE_PATH)/vis_slim_config.yaml $(KUBE_NAMESPACE)/ds-cbfcontroller-controller-0:/app/mnt/slim/vis_slim_config.yaml
	@echo "Successfully copied Talon HW config file to the CBF Controller Pod."

## TARGET: itf-cbf-copy-hw-config
## SYNOPSIS: make itf-cbf-copy-config
## HOOKS: none
## VARS:
##      MCS_CONFIG_FILE_PATH=[hw_config.yaml init_sys_param.json internal_params.json folder path] (default value: resources/mcs)
##      KUBE_NAMESPACE=[kubernetes namespace where MCS is deployed] (default value: integration)
##  make target for configuring the MCS - specifically HW config

itf-cbf-copy-hw-config: ## Copy the Talon HW Config file onto a pod
	@kubectl cp $(MCS_CONFIG_FILE_PATH)/hw_config.yaml $(KUBE_NAMESPACE)/ds-cbfcontroller-controller-0:/app/mnt/hw_config/hw_config.yaml
	@echo "Successfully copied Talon HW config file to the CBF Controller Pod."

## TARGET: itf-cbf-power-on
## SYNOPSIS: make itf-cbf-power-on
## HOOKS: none
## VARS: 
##	HW_CONFIG_FILE_PATH=[scripts path] (default value: resources/talon)
##  make target for switching on the TalonDx using the PDU's SSH terminal via the APC bash script from CIPA Team

itf-cbf-power-on: # APC scripts to power on the TalonDx
	@[[ -f  $(HW_CONFIG_FILE_PATH)/talon_power_apc.sh ]] || exit 404;
	@cd $(HW_CONFIG_FILE_PATH) && \
	./talon_power_apc.sh lru1 on && \
	./talon_power_apc.sh lru2 on

## TARGET: itf-cbf-tango-on
## SYNOPSIS: make itf-cbf-tango-on
## HOOKS: none
## VARS: 
##	KUBE_NAMESPACE=[kubernetes namespace where MCS is deployed] (default value: integration)
##  CLUSTER_DOMAIN=[domain of the cluster where the MCS is running] (default value: miditf.internal.skao.int)
##  make target for switching on all the TalonDx' under control of the CSP.LMC

itf-cbf-tango-on:
	@export TANGO_HOST=tango-databaseds.$(KUBE_NAMESPACE).svc.$(CLUSTER_DOMAIN):10000 && \
	talon_on

## TARGET: itf-cbf-setup
## SYNOPSIS: make itf-cbf-setup
## HOOKS: none
## VARS: 
##	KUBE_NAMESPACE=[kubernetes namespace where MCS is deployed] (default value: integration)
##	HW_CONFIG_FILE_PATH=[scripts path] (default value: resources/talon)
##	TALON_BOARD_IDX=[Talon board index number] (default value: 1)
##  make target for registering the deviceservers in the TangoDB.


itf-cbf-setup: itf-cbf-talonlru-off itf-cbf-config-mcs  itf-cbf-tango-on
