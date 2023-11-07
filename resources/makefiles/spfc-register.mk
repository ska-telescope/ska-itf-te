## TARGET: register-spfc
## SYNOPSIS: make register-spfc
## HOOKS: none
## VARS: none
##  make target for registering SPFC to the tango database.

SERVICE_NAME ?= tango-databaseds
NAMESPACE ?= dish-lmc-ska001
TANGO_HOST = 10.164.10.22:10000
SPFC_HOST ?= 10.165.3.33
DEVICE_LOCATION ?= ska000
TANGO_HOST_CONFIG ?= resources/spfc/tango_host.ini
SPFC_CONFIG ?= resources/spfc/spfc_config.ini

#Write config parameters to the file
update-spfc-config:
	@touch $(TANGO_HOST_CONFIG)
	@echo "[Hosts]" >> $(TANGO_HOST_CONFIG)
	@echo "TANGO_HOST="$(TANGO_HOST) >> $(TANGO_HOST_CONFIG)
	@scp $(TANGO_HOST_CONFIG) skao@$(SPFC_HOST):/home/skao/tango_host.ini
	@rm $(TANGO_HOST_CONFIG)
	sleep 8

restart-spfc-service:
	@ssh skao@$(SPFC_HOST) -t "sudo /bin/systemctl restart spfc-system.target"

#SPFC serial number, for exmaple 4F0001 (found in /var/lib/spfc/spfc/spfc_config.ini within SPFC device
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
