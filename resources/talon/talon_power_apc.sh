#!/bin/bash

LRU=$1
STATE=$2

DIR_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

APC_PDU_SCRIPT=".${DIR_PATH}/apc_pdu.expect"
echo "###&&&### APC PDU Script located at ${APC_PDU_SCRIPT} ###&&&###"

USAGE_BANNER="Usage: ./talon_power_lru.sh LRU [STATE]
  LRU: lru1

  Options:
    [STATE]: on|On|ON|off|Off|OFF (sets the lru to the STATE; if no STATE is provided, the LRU status is returned)"

if ! [[ "$LRU" =~ lru1 ]]; then
	echo "ERROR: Unrecognized LRU \"$LRU\" provided."
        echo "$USAGE_BANNER"
        exit 1
fi

# OUTLET1 and OUTLET2 are the outlet IDs.
# - for APC, valid range is 1 to 24

if [[ "$LRU" == "lru1" ]]; then
	OUTLET1="12"
	OUTLET2="13"
else
	echo "ERROR: Unknown LRU \"$LRU\". No OUTLETS assigned."
	exit 1
fi


if [[ "$STATE" =~ on|On|ON ]]; then
	$APC_PDU_SCRIPT on $OUTLET1 $OUTLET2
elif [[ "$STATE" =~ off|Off|OFF ]]; then
	$APC_PDU_SCRIPT off $OUTLET1 $OUTLET2
elif [[ "$STATE" == "" ]]; then
	$APC_PDU_SCRIPT status $OUTLET1 $OUTLET2
else
	echo -e "ERROR: Unrecognized STATE \"$STATE\" provided.\n"
	echo "$USAGE_BANNER"
	exit 1
fi

