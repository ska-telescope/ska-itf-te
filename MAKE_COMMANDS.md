```sh
cd $(HW_CONFIG_FILE_PATH) && ./talon_power_apc.sh lru1 && ./talon_power_apc.sh lru2
sleep 1

cd $(HW_CONFIG_FILE_PATH) && ./talon_power_apc.sh lru1 off && ./talon_power_apc.sh lru2 off
sleep 3

cd $(HW_CONFIG_FILE_PATH) && ./talon_power_apc.sh lru1 on && ./talon_power_apc.sh lru2 on
sleep 45

kubectl cp -n ${CBF_BITSTREAM_RPD_SOURCE_POD_NAMESPACE} ${CBF_BITSTREAM_RPD_SOURCE_POD}:${CBF_BITSTREAM_RPD_SOURCE_FILEPATH} ${CBF_EC_MOUNT_PATH}/${CBF_BITSTREAM_RPD_FILENAME}

kubectl cp $(SLIM_CONFIG_FILE_PATH)/fs_slim_config.yaml staging/ds-cbfcontroller-controller-0:/app/mnt/slim/fs/slim_config.yaml

kubectl cp $(SLIM_CONFIG_FILE_PATH)/vis_slim_config.yaml staging/ds-cbfcontroller-controller-0:/app/mnt/slim/vis/slim_config.yaml

kubectl cp $(MCS_CONFIG_FILE_PATH)/hw_config.yaml staging/ds-cbfcontroller-controller-0:/app/mnt/hw_config/hw_config.yaml

kubectl cp $(MCS_CONFIG_FILE_PATH)/internal_params.json staging/ds-vcc-vcc-0:/app/mnt/vcc_param/internal_params_receptor1_band1.json
sleep 3

export TANGO_HOST=tango-databaseds.staging.svc.$(CLUSTER_DOMAIN):10000 && talon_on
sleep 3
```

## talon_on call path and operations

Call path used by this repo:

```text
make itf-cbf-tango-on
export TANGO_HOST=tango-databaseds.staging.svc.$(CLUSTER_DOMAIN):10000 && talon_on
talon_on -> src.ska_mid_itf_engineering_tools.cbf_config.talon_on:main
```

What talon_on then calls (in order):

```python
ec_deployer=DeviceProxy("mid_csp_cbf/ec/deployer")
ec_deployer.targetTalons = [1, 2, 3, 4]
ec_deployer.generate_config_jsons()
ec_deployer.set_timeout_millis(600000)
ec_deployer.download_artifacts()  # unless DOWNLOAD_CBF_BITSTREAMS is false/0
ec_deployer.configure_db()
ec_deployer.set_timeout_millis(3000)
```

Pipeline-specific behavior here:

```text
In .gitlab/ci/.jobs.yaml, SWITCH_CSP_ON is set to "false", so the CSP ON branch in talon_on.py is skipped.
talon_on performs EC deployer configuration/artifact/database steps above, then exits without calling csp.on([]).
```
