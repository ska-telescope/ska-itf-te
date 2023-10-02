import subprocess
import sys
import tango
from tango import Database, DbDevInfo

def main():
    dev_info1 = DbDevInfo()
    print(tango.ApiUtil.get_env_var("TANGO_HOST"))
    dev_info1.name = 'mid-itf/SpfcLocation/1'
    dev_info1._class = 'SpfcLocation'
    dev_info1.server = 'SpfcLocation/test'

    dish_lmc_ip_address = sys.argv[1]    
    print("Resolved IP address:" + str(dish_lmc_ip_address))
    data_base = Database("10.164.10.22", 10000)
    data_base.add_server(dev_info1.server, dev_info1, with_dserver=True)
    dev_info = data_base.get_device_info(dev_info1.name)
    print("Registered device=" + str(dev_info))

if __name__ == "__main__":
    main()

#tango_admin --add-server DeviceWithProperty/test DeviceWithProperty foo/bar/1