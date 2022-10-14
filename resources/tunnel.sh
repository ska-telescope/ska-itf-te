#!/bin/bash

FILE=resources/OpenSSHPorts.mak

# if [ "$1" == "close" ]; then
#     kill $2;
# fi

if [ ! -f "$FILE" ]; then
    touch $FILE
    echo "SSH_PORT_6443_PROCESS_ID=
SSH_PORT_8080_PROCESS_ID=
SSH_PORT_8000_PROCESS_ID=
SSH_PORT_2234_PROCESS_ID=" >> $FILE

fi

ssh -N -L $1:$2:$3 pi@mid-itf.duckdns.org -p 2322 &
PID=$!
sed -i -e "s/SSH_PORT_$1_PROCESS_ID=.*/SSH_PORT_$1_PROCESS_ID=$PID/" $FILE
rm $FILE-e || true
