# Archiver Config Generation Guide

This file exists to help an LLM generate a new dish EDA (Engineering Data Archiver) config
YAML file, in the style of [dish-lmc-ska001-config.yml](dish-lmc-ska001-config.yml), for a
new dish. The YAML format is documented at:
https://developer.skao.int/projects/ska-eda-yaml2archiving/en/latest/yam2archiving.html#example-yaml-configuration

## Before you start

**When a user asks for a new archiver config file, first ask which hardware devices are to
be archived**, using the hardware subsystem names below as options. Do not generate a config until
the user has confirmed the device selection.

## Unique TRLs (hardware devices) in the SKA001 reference config

Each attribute `trl` in the config is `<device_trl>/<attribute_name>`. The unique device
TRLs (i.e. hardware devices), with their subsystem names, are:

| Subsystem name | Tango Device TRL |
| --- | --- |
| SPFC (SPF Controller) | `ska001/spf/spfc` |
| SPFRx (SPF Receiver Controller) | `ska001/spfrxpu/controller` |
| Dish Manager | `mid-dish/dish-manager/ska001` |
| DS Manager (Dish Structure Manager) | `mid-dish/ds-manager/ska001` |

## Procedure for generating/filtering a dish config

Given a reference config (e.g. [dish-lmc-ska001-config.yml](dish-lmc-ska001-config.yml)) and a
target dish ID (e.g. `ska046`), plus the confirmed subsystem selection:

1. Copy the `tango_hosts`, `configuration_managers`, and `defaults` sections as-is, only
   updating the dish ID in the `tango_hosts.host` value.
2. Filter the `attributes` list to only the entries whose `trl` device prefix matches one of
   the selected subsystem TRLs (substituting the dish ID), preserving the original relative
   order of the remaining attributes and all their `configuration` fields unchanged.
3. Only after step 2, determine which `es` (event subscriber) values are actually referenced
   by the **filtered** attributes, then trim `event_subscribers` to only those entries (keep
   their original `esN`/`mid-eda/es/NN` numbering, do not renumber).
4. Substitute the dish ID into every `trl` in the filtered attributes.

### Critical: do not trim `event_subscribers` and `attributes` separately

Steps 2 and 3 must both be done, and step 3 must be derived from the result of step 2, not
from the original unfiltered file. Trimming `event_subscribers` alone (or before filtering
`attributes`) leaves `attributes` entries with an `es:` value that no longer exists in
`event_subscribers` — this is a broken config, not a harmless leftover, and the docs give no
fallback behavior for a dangling `es` reference.

For a config this size, do **not** attempt this with manual string edits — use a script (e.g.
Python + PyYAML) to load the YAML, filter `attributes` by `trl` prefix, derive the used `es`
set from the filtered attributes, filter `event_subscribers` to that set, and write the file
back. Manual/partial edits on a large file are how this bug was introduced previously.

Before finishing, verify: every `es` value used in `attributes` has a matching entry in
`event_subscribers` (and vice versa, no orphaned unused subscribers left behind).
