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

SERVICE_NAME ?= tango-databaseds
NAMESPACE ?= dish-lmc-ska001
TANGO_HOST = 10.164.10.22:10000
SPFC_HOST ?= 10.165.3.28
DEVICE_LOCATION ?= ska002
#The following two lines need not to be changed.
TANGO_HOST_CONFIG ?= resources/spfc/tango_host.ini
SPFC_CONFIG ?= resources/spfc/spfc_config.ini

#Write config parameters to the SPFC's file
update-spfc-config:
	@touch $(TANGO_HOST_CONFIG)
	@echo "[Hosts]" >> $(TANGO_HOST_CONFIG)
	@echo "TANGO_HOST="$(TANGO_HOST) >> $(TANGO_HOST_CONFIG)
	@scp $(TANGO_HOST_CONFIG) skao@$(SPFC_HOST):/home/skao/tango_host.ini
	@rm $(TANGO_HOST_CONFIG)
	sleep 8

restart-spfc-service:
	@ssh skao@$(SPFC_HOST) -t "sudo /bin/systemctl restart spfc-system.target"

#Get the config file with serial number, for exmaple 4F0001 (found in /var/lib/spfc/spfc/spfc_config.ini within SPFC device
get-spfc-serial:
	@scp skao@$(SPFC_HOST):/var/lib/spfc/spfc/spfc_config.ini resources/spfc
	@sleep 5

register-spfc:
	@make update-spfc-config
	@make $(restart-spfc-service)
	@sleep 10
	@make get-spfc-serial
	@python3 scripts/spfc/register_device.py $(TANGO_HOST) $(DEVICE_LOCATION) $(SPFC_HOST)
	@sleep 6
	@echo "Registration done."
	@echo "Restarting SPFC"
	@make $(restart-spfc-service)
	@sleep 10
	@rm $(SPFC_CONFIG)
