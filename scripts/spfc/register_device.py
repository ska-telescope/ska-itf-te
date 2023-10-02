import subprocess
import sys
import tango
from tango import Database, DbDevInfo

def main():
    dev_info1 = DbDevInfo()
    print(tango.ApiUtil.get_env_var("TANGO_HOST"))
    dev_info1.name = 'SPFRx/rxpu/controller'
    dev_info1._class = 'SPFRx'
    dev_info1.server = 'SPFRx/test'
    try:
        dish_lmc_ip_address = sys.argv[1]
        database = Database(str(dish_lmc_ip_address), 10000)
        database.add_server(dev_info1.server, dev_info1, with_dserver=True)
        dev_info = database.get_device_info(dev_info1.name)
        print(f"Registered device is {str(dev_info)} ")
    except IndexError:
        print(f"Error: Please call  \' {str(sys.argv) } \' with ip address argument.")

if __name__ == "__main__":
    main()