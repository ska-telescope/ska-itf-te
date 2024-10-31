#!/bin/bash

set -o pipefail

DASH_BOARD_FILE="$1"
FIND_DISH_ID=$2
REPLACE_DISH_ID=$3

echo "DASH_BOARD_FILE=${DASH_BOARD_FILE}"
echo "FIND_DISH_ID=${FIND_DISH_ID}"
echo "REPLACE_DISH_ID=${REPLACE_DISH_ID}"

if [[ -z ${DASH_BOARD_FILE} || -z  ${FIND_DISH_ID} || -z ${REPLACE_DISH_ID} ]];
then
    echo "Usage: update_dashboard.sh dashboard name.wj, SKA001, SKA036 (where we replace SKA001 eith SKA036)"
    exit 1
fi

echo "Replacing ${FIND_DISH_ID} with ${REPLACE_DISH_ID} in ${DASH_BOARD_FILE}"

#String replace regardless of letter case 
#To lower case
sed -i "s/${FIND_DISH_ID,,}/${REPLACE_DISH_ID}/g" "${DASH_BOARD_FILE}"
#To upper case
sed -i "s/${FIND_DISH_ID^^}/${REPLACE_DISH_ID}/g" "${DASH_BOARD_FILE}"

#Rename the dashboard
ADD_DISH_ID=${DASH_BOARD_FILE/.wj/}
#The following lines below, ensures that string replace works regardless of letter case.
#To lower case
NEW_FILE_NAME=${ADD_DISH_ID/"${FIND_DISH_ID,,}"/${REPLACE_DISH_ID}.wj}
#To upper case
NEW_FILE_NAME=${ADD_DISH_ID/"${FIND_DISH_ID^^}"/${REPLACE_DISH_ID}.wj}


echo $NEW_FILE_NAME
mv "${DASH_BOARD_FILE}" ./"${NEW_FILE_NAME}"