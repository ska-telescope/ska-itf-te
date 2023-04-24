#!/bin/sh

ansible-playbook -i inventory_ssh_keys distribute_ssh_keys.yml \
      -e @./ssh_key_vars.yml
