#!/usr/bin/bash

declare -a SECRET_PATHS


read_secrets()
{
    SECRET_PATH=$1
    echo "Read path $SECRET_PATH"
    vault kv list $SECRET_PATH | tail +3 | while read PATH
    do
        if [ -z $PATH ]
        then
            return
        fi
        echo -e "\t *** $PATH ***"
        # read_secrets $SECRET_PATH/$PATH
    done
}

if [ -z $VAULT_ADDR ]
then
    export VAULT_ADDR="https://vault.skao.int/"
fi

MID_AIV_SECRETS=("cubbyhole/" "dev/" "mid-aa/" "mid-itf/" "shared/")
for MID_AIV_SECRET in ${MID_AIV_SECRETS[@]}
do
    echo "Read $MID_AIV_SECRET"
    read_secrets $MID_AIV_SECRET
    echo
done
