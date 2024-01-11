#!/usr/bin/python
import os
import datetime, json
from tango import DeviceProxy, Database

# Take the namespace name from the deployment job
KUBE_NAMESPACE = "ci-ska-mid-itf-at-1839-sdp-deploy"
# KUBE_NAMESPACE = "integration"
CLUSTER_DOMAIN = "miditf.internal.skao.int"
# set the name of the databaseds service
DATABASEDS_NAME = "tango-databaseds"

tango_host = f"{DATABASEDS_NAME}.{KUBE_NAMESPACE}.svc.{CLUSTER_DOMAIN}:10000"
print("Tango host %s" % tango_host)

# finally set the TANGO_HOST
# os.environ["TANGO_HOST"] = tango_host

TIMEOUT=60

database = Database()
instance_list = database.get_device_exported("*")
print("%d devices avalable" % (len(instance_list)))
for instance in instance_list.value_string:
    dev = DeviceProxy(instance)
    print(instance)
    print("*****")
    print(dev.info())

CSP = DeviceProxy("mid-csp/control/0")

print(f"Admin mode          : {CSP.adminmode}")
print(f"State               : {CSP.State()}")

print("Activate CSP")
CSP.adminmode=0
print(f"Admin mode          : {CSP.adminmode}")
print(f"State               : {CSP.State()}")
# CSP.adminmode

# Check CBF SimulationMode

print(f"CBF Simulation Mode : {CSP.cbfSimulationMode}")

print(f"Set timeout to {TIMEOUT}")
CSP.commandTimeout=TIMEOUT
print(f"Timeout             : {CSP.commandTimeout}")

print("Send the ON command")
CSP.on([])

print("Now check if all the devices are switched on as they should be.")

print("Set up a Tango DeviceProxy to the CSP Subarray device")
CSPSubarray=DeviceProxy('mid-csp/subarray/01')

resources=json.dumps({
    "subarray_id": 1,
    "dish":{
        "receptor_ids":["SKA001"]
    }
})

print(f"Assign resources {resources}")
CSPSubarray.AssignResources(resources)


print("Copy the output of the next print line and paste into your shell.")
print(f"kubectl -n {KUBE_NAMESPACE} exec ec-bite -- python3 midcbf_bite.py --talon-bite-lstv-replay --boards=1")

# Generate the Delaymodel and check if it was was correctly sent:
sub = DeviceProxy(\"ska_mid/tm_leaf_node/csp_subarray_01")
current_time = float(datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).timestamp())
dm={
	"interface": "https://schema.skao.int/ska-csp-delaymodel/2.2",
	"epoch": current_time,
	"validity_period": 400.0,
	"delay_details": [{
		"receptor": "SKA001",
		"poly_info": [{
			"polarization": "X",
			"coeffs": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]},
			{"polarization": "Y", "coeffs": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}
	]}
]}
sub.delayModel=json.dumps(dm)
assert sub.delayModel==json.dumps(dm), f"Expected {dm}, got\n{sub.delayModel}"

print("By now, we are supposed to look at the output of `tcpdump -i net1` in the SDP Surrogate pod and see data!")

print("End Scan (CSP Subarray)")
print(
	"If this fails because things were in READY, that means you didn't need to run it now - DON'T PANIC!\n"
	"Run this if device is in "
)
print(f"{CSPSubarray.EndScan()}")

print("Go to idle")
CSPSubarray.GoToIdle()
print(f"{CSPSubarray.obsState}")

print("## Release Resources (CSP Subarray)")
CSPSubarray.ReleaseAllResources()

print("Final Teardown")
# Check with make itf-cbf-talonlru-status - lru should be off now
CSP.off([])
CSP.cbfSimulationMode=True
CSP.commandTimeout=3
CSP.adminmode=1
