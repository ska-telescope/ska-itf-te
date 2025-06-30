#!/bin/bash

LRU=$1
STATE=$2
SSH_TIMEOUT_IN_SECONDS="5"
SLEEP_TIMEOUT_FOR_SHUTDOWN_CMD="15"

DIR_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

# Get Talon IP addresses from hw_config.yaml
HW_CONFIG_YAML="../mcs/hw_config.yaml"

APC_PDU_SCRIPT=./apc_pdu.expect

USAGE_BANNER="Usage: ./talon_power_lru.sh LRU [STATE]
  LRU: lru1 or lru2

  Options:
    [STATE]: on|On|ON|off|Off|OFF (sets the lru to the STATE; if no STATE is provided, the LRU status is returned)"

if ! [[ "$LRU" =~ lru1 || "$LRU" =~ lru2 ]]; then
	echo "ERROR: Unrecognized LRU \"$LRU\" provided."
        echo "$USAGE_BANNER"
        exit 1
fi

# OUTLET1 and OUTLET2 are the outlet IDs.
# - for APC, valid range is 1 to 24

if [[ "$LRU" == "lru1" ]]; then
	OUTLET1="17"
	OUTLET2="18"
	TALON_A=$(yq '.talon_board["001"]' "$HW_CONFIG_YAML")
	TALON_B=$(yq '.talon_board["002"]' "$HW_CONFIG_YAML")
elif [[ "$LRU" == "lru2" ]]; then
	OUTLET1="12"
	OUTLET2="13"
	TALON_A=$(yq '.talon_board["003"]' "$HW_CONFIG_YAML")
	TALON_B=$(yq '.talon_board["004"]' "$HW_CONFIG_YAML")
else
	echo "ERROR: Unknown LRU \"$LRU\". No OUTLETS assigned."
	exit 1
fi


if [[ "$STATE" =~ on|On|ON ]]; then
	$APC_PDU_SCRIPT on $OUTLET1 $OUTLET2
elif [[ "$STATE" =~ off|Off|OFF ]]; then
	echo "Shutting down ${TALON_A}..."
	ssh -o ConnectTimeout=$SSH_TIMEOUT_IN_SECONDS root@${TALON_A} -n shutdown now
	echo "Shutting down ${TALON_B}..."
	ssh -o ConnectTimeout=$SSH_TIMEOUT_IN_SECONDS root@${TALON_B} -n shutdown now
	echo "Sleeping for ${SLEEP_TIMEOUT_FOR_SHUTDOWN_CMD} seconds..."
	sleep $SLEEP_TIMEOUT_FOR_SHUTDOWN_CMD

	$APC_PDU_SCRIPT off $OUTLET1 $OUTLET2
elif [[ "$STATE" == "" ]]; then
	$APC_PDU_SCRIPT status $OUTLET1 $OUTLET2
else
	echo -e "ERROR: Unrecognized STATE \"$STATE\" provided.\n"
	echo "$USAGE_BANNER"
	exit 1
fi

