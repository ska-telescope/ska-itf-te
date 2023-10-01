import subprocess
import tango
from tango import Database, DbDevInfo

def main():
    dev_info1 = DbDevInfo()
    print(tango.ApiUtil.get_env_var("TANGO_HOST"))
    dev_info1.name = 'mid-itf/SpfcLocation/1'
    dev_info1._class = 'SpfcLocation'
    dev_info1.server = 'SpfcLocation/test'

    ip_address = subprocess.run(["kubectl", "get", "--namespace", "dish-lmc-ska001", "service", "tango-databaseds", "-o",
                             "jsonpath={'.status.loadBalancer.ingress[0].ip'}"], check=False, shell=True, capture_output=True, text=True)
    
    print("Reolved IP address:{}".format(str(ip_address.stdout)))
    db = Database("10.164.10.22", 10000)
    db.add_server(dev_info1.server, dev_info1, with_dserver=True)
    dev_info = db.get_device_info(dev_info1.name)
    print("Registered device=" + str(dev_info))

if __name__ == "__main__":
    main()

#tango_admin --add-server DeviceWithProperty/test DeviceWithProperty foo/bar/1