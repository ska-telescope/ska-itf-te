# distribute-ssh-keys

Update keys on Systems Team inventory

## Summary

This repo adds and removes ssh keys across the System Teams managed inventory.

Checkout distribute-ssh-keys (this repo):
```
git clone git@gitlab.com:ska-telescope/sdi/distribute-ssh-keys.git
cd distribute-ssh-keys
```
Update `ssh_key_vars.yml` as the input for `add_ssh_keys` and `remove_ssh_keys`.

In order for this tool to work for you, you must already have `ssh` access to the inventory described in `inventory_ssh_keys`.

## Add keys to all inventory
 
To add the configured keys in `add_ssh_keys` to hosts, run:
```
$ make add
```

## Remove keys from all inventory
 
To remove the configured keys in `remove_ssh_keys` from hosts, run:
```
$ make remove
```

## Limiting

To limit the scope of inventory updated, set `NODES` to the appropriate inventory group, eg:
```
$ make add NODES=v1
```
This would add the list of keys to nodes in the `v1` Kubernetes cluster as described by the `inventory_ssh_keys` file.


Run `make` to get the help:
```
$ make
make targets:
add                            Add keys
help                           show this help.
lint                           Lint check playbook
remove                         Remove keys
vars                           Variables

make vars (+defaults):
INVENTORY_FILE                 ./inventory_ssh_keys
NODES                          nodes ## subset of hosts from inventory to run against
PRIVATE_VARS                   ./ssh_key_vars.yml
```
