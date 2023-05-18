#!/usr/bin/env bash

set -eux
set -o pipefail

groups="atlas"
for group in ${groups}
    if [ ${group} != "sudo" ]; then
        groupadd ${group}
    fi
done

users="a.debeer g.leroux j.coetzer n.nzotho p.jordaan t.tsotetsi"
for user in ${users}
do
    useradd -m ${user}
    echo "${user}:${user}" | chpasswd
    for group in ${groups}
        adduser ${user} ${group}
    done
done

