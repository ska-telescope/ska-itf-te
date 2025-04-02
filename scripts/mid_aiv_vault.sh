#!/usr/bin/bash

# declare -a SECRET_PATHS


read_secrets()
{
    SECRET_PATH=$1
    echo "Read path $SECRET_PATH"
    while read -r PATH
    do
        if [ -z $PATH ]
        then
            return
        fi
        PATH_CHK="${PATH: -1}"
        # echo -e "\t *** $PATH ($PATH_CHK) ***"
        if [ "$PATH_CHK" = "/" ]
        then
            SECRET_PATHS+=( "${SECRET_PATH}${PATH}" )
            echo -e "\tAdd path $PATH"
        else
            SECRET_PATHS+=( "${SECRET_PATH}${PATH}" )
            echo -e "\tAdd $PATH"
        fi
        # read_secrets $SECRET_PATH/$PATH
    done < <(/usr/bin/vault kv list $SECRET_PATH | /usr/bin/tail +3)
}

if [ -z $VAULT_ADDR ]
then
    export VAULT_ADDR="https://vault.skao.int/"
fi

SECRET_PATHS=()
MID_AIV_SECRETS=("cubbyhole/" "dev/" "mid-aa/" "mid-itf/" "shared/")
for MID_AIV_SECRET in ${MID_AIV_SECRETS[@]}
do
    # echo "Read $MID_AIV_SECRET"
    read_secrets $MID_AIV_SECRET
    echo
done
echo "______________________________"
for SECRET_PATH in ${SECRET_PATHS[@]}
do
    PATH_CHK="${SECRET_PATH: -1}"
    if [ "$PATH_CHK" = "/" ]
    then
        # echo "Read $SECRET_PATH"
        read_secrets $SECRET_PATH
    fi
done
echo "______________________________"
for SECRET_PATH in ${SECRET_PATHS[@]}
do
    PATH_CHK="${SECRET_PATH: -1}"
    if [ "$PATH_CHK" = "/" ]
    then
        # echo "Read $SECRET_PATH"
        read_secrets $SECRET_PATH
    fi
done
echo "______________________________"
for SECRET_PATH in ${SECRET_PATHS[@]}
do
    echo $SECRET_PATH
done
