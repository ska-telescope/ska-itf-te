## Step 1: Check Talon status

Called using `make itf-cbf-talonlru-status`

~~~sh
cd $(HW_CONFIG_FILE_PATH) && ./talon_power_apc.sh lru1 && ./talon_power_apc.sh lru2
~~~

## Step 2: Switch Talon LRUs off

Called using `make itf-cbf-talonlru-off`

~~~sh
cd $(HW_CONFIG_FILE_PATH) && ./talon_power_apc.sh lru1 off && ./talon_power_apc.sh lru2 off
~~~

## Step 3: Switch Talon LRUs on

Called using `make itf-cbf-talonlru-on`

~~~sh
cd $(HW_CONFIG_FILE_PATH) && ./talon_power_apc.sh lru1 on && ./talon_power_apc.sh lru2 on
~~~

## Step 4: Copy CBF bitstream RPD

Called using `make copy-cbf-bitstream-rpd`

~~~sh
kubectl cp -n ${CBF_BITSTREAM_RPD_SOURCE_POD_NAMESPACE} ${CBF_BITSTREAM_RPD_SOURCE_POD}:${CBF_BITSTREAM_RPD_SOURCE_FILEPATH} ${CBF_EC_MOUNT_PATH}/${CBF_BITSTREAM_RPD_FILENAME}
~~~

## Step 5: Copy SLIM FS config

Called using `make itf-cbf-copy-slim-config` (dependency of `make itf-cbf-config-mcs`)

~~~sh
kubectl cp $(SLIM_CONFIG_FILE_PATH)/fs_slim_config.yaml staging/ds-cbfcontroller-controller-0:/app/mnt/slim/fs/slim_config.yaml
~~~

## Step 6: Copy SLIM VIS config

Called using `make itf-cbf-copy-slim-config` (dependency of `make itf-cbf-config-mcs`)

~~~sh
kubectl cp $(SLIM_CONFIG_FILE_PATH)/vis_slim_config.yaml staging/ds-cbfcontroller-controller-0:/app/mnt/slim/vis/slim_config.yaml
~~~

## Step 7: Copy HW config

Called using `make itf-cbf-copy-hw-config` (dependency of `make itf-cbf-config-mcs`)

~~~sh
kubectl cp $(MCS_CONFIG_FILE_PATH)/hw_config.yaml staging/ds-cbfcontroller-controller-0:/app/mnt/hw_config/hw_config.yaml
~~~

## Step 8: Copy internal params

Called using `make itf-cbf-config-mcs`

~~~sh
kubectl cp $(MCS_CONFIG_FILE_PATH)/internal_params.json staging/ds-vcc-vcc-0:/app/mnt/vcc_param/internal_params_receptor1_band1.json
~~~

## Step 9: Run Talon Tango ON entrypoint

Called using `make itf-cbf-tango-on`

~~~sh
export TANGO_HOST=tango-databaseds.staging.svc.$(CLUSTER_DOMAIN):10000 && talon_on
~~~

talon_on console script entry point:

~~~text
src.ska_mid_itf_engineering_tools.cbf_config.talon_on:main
~~~

talon_on calls in this path:

~~~python
ec_deployer = DeviceProxy("mid_csp_cbf/ec/deployer")
ec_deployer.targetTalons = [1, 2, 3, 4]
ec_deployer.generate_config_jsons()
ec_deployer.set_timeout_millis(600000)
ec_deployer.download_artifacts()  # unless DOWNLOAD_CBF_BITSTREAMS is false/0
ec_deployer.configure_db()
ec_deployer.set_timeout_millis(3000)
~~~

Pipeline behavior for this path:

~~~text
SWITCH_CSP_ON is false in CI, so the CSP ON branch is skipped.
~~~

