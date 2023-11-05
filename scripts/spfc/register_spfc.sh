 #!/bin/bash
export SERVICE_NAME=tango-databaseds
export NAMESPACE="dish-lmc-ska001"
export TANGO_HOST="10.164.10.22:10000"
export SPFC_HOST="10.165.3.28"
export DEVICE_LOCATION="ska002"
#update SPFC's config file
scp resources/ansible-playbooks/roles/update_spfc/templates/tango_host.ini.j2 skao@${SPFC_HOST}:/home/skao/tango_host.ini
#Install register SPFC
export SPFC_SERIAL=$(ssh -t skao@${SPFC_HOST} "grep -A1 "Serial_Nr" /var/lib/spfc/spfc/spfc_config.ini | grep "SPFC"")
python scripts/spfc/register_device.py ${TANGO_HOST} ${DEVICE_LOCATION} ${SPFC_SERIAL}
ssh skao@${SPFC_HOST} -t "sudo /bin/systemctl restart spfc-system.target"