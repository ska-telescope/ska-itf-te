#!/bin/bash

FILE=resources/OpenSSHPorts.mak
if [ ! -f "$FILE" ]; then
    echo
    echo "ERROR: No file named $FILE exists."
    echo "       First run"
    echo "###### make open-tunnel ##########"
    echo "(which will fail) and then try again."
    echo
    exit 1
fi
. $FILE
PID=$(IFS="="; echo $(cat $FILE | grep $1) | awk '{print $NF}')
echo "Process ID: $PID"
kill $PID || echo "Failure killing PID $(PID)"
sed -i -e "s/SSH_PORT_$1_PROCESS_ID=.*/SSH_PORT_$1_PROCESS_ID=/" $FILE
rm $FILE-e
