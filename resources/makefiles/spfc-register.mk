## TARGET: register-spfc
## SYNOPSIS: make register-spfc
## HOOKS: none
## VARS: 
##		SERVICE_NAME: name of the tango database service to register SPFC into
##		NAMESPACE: name of the namespace of the existing deployment the SPFC will use
##		TANGO_HOST: IP and port number of the tango database that we will register the SPFC into.
##					In order to get and set the TANGO_HOST variable with the tango database IP under 
##					specified service name and namespace you can run the following command:
##					export TANGO_HOST=$(kubectl -n ${NAMESPACE} get svc ${SERVICE_NAME} -o jsonpath={.status.loadBalancer.ingress[0].ip})
##		SPFC_HOST: IP address of the SPFC device we want to register to tango database
##		DEVICE_LOCATION: location of the SPFC device, as it appears in the device name for example ska000/spf/spf1.
##						 ska000 is the device location
##		TANGO_HOST_CONFIG: Config file residing within the SPFC that contains the SPFC's unique serial number
##		SPFC_CONFIG: Tango host configuration information that with tango database server where SPFC will be registered to.
##  make target for registering SPFC to the tango database.
##  Please ensure that the TANGO_HOST variable is set before running the register-spfc command.

# set the following variables within the PrivateRules.mak file

SERVICE_NAME ?= tango-databaseds
NAMESPACE ?= dish-namespace
TANGO_HOST ?= tango-ip:port
SPFC_HOST ?= spfc-host
SPFC_USER ?= spfc-user
DEVICE_LOCATION ?= dish-index
SPFC_STATUS ?= 
#The following two lines need not to be changed.
TANGO_HOST_CONFIG ?= resources/spfc/tango_host.ini
SPFC_CONFIG ?= resources/spfc/spfc_config.ini

#Write config parameters to the SPFC's file
update-spfc-config:
	@touch $(TANGO_HOST_CONFIG)
	@echo "[Hosts]" >> $(TANGO_HOST_CONFIG)
	@echo "TANGO_HOST="$(TANGO_HOST) >> $(TANGO_HOST_CONFIG)
	@scp $(TANGO_HOST_CONFIG) skao_user@$(SPFC_HOST):/home/skao_user/tango_host.ini
	@rm $(TANGO_HOST_CONFIG)
	sleep 8

restart-spfc-service:
	@ssh skao_user@$(SPFC_HOST) -t "sudo /bin/systemctl restart spfc-system.target"

#Get the config file with serial number, for example 4F0001 (found in /var/lib/spfc/spfc/spfc_config.ini within SPFC device
get-spfc-serial:
	@scp skao_user@$(SPFC_HOST):/var/lib/spfc/spfc/spfc_config.ini resources/spfc
	@sleep 5

get-service-status:
	@secs ?= 10
	while [ $${secs} -gt 0 ] ; do
		SPFC_STATUS=$(ssh $(SPFC_USER)@$(SPFC_HOST) -t "/bin/systemctl is-active --quiet spfc-system.target")
		secs=`expr $$secs - 1`;
		@if [[ -z "${SPFC_STATUS}" ]];then
			break
		fi;
	done;
	@if [[ "*$$not loaded*" == "$(SPFC_STATUS)" ]];then
		echo 'SPFC spfc-system.target is not loaded.';
		exit 0;
	@fi

register-spfc:
	@make update-spfc-config
	@make restart-spfc-service
	@make get-service-status
	@
	@make get-spfc-serial
	@python3 scripts/spfc/register_device.py $(TANGO_HOST) $(DEVICE_LOCATION) $(SPFC_HOST)
	@echo "Registration done."
	@echo "Restarting SPFC"
	@make $(restart-spfc-service)
	@get-service-status
	@rm $(SPFC_CONFIG)
