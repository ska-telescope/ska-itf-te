import os
import subprocess
import sys
import tango
from time import sleep
from tango import Database, DbDevInfo,DeviceProxy
import threading
import logging as log_test

def register_all_devices():
    tango_db_env = str(tango.ApiUtil.get_env_var("TANGO_HOST"))
    print(tango_db_env)
    tango_db_ip = str(tango_db_env.split(":")[0])
    tango_db_port = int(tango_db_env.split(":")[1])
    database = Database(tango_db_ip, tango_db_port)
    dev_info = DbDevInfo()
    logname = "register_spfc_logs.log"

    log_test.basicConfig(filename=logname,
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=log_test.DEBUG)

    ls_device_names = ["spfc", "spf1", "spf2", "spf345", "spfhe", "spfvac"]
    for dev in ls_device_names:
        print(f"===Registering device:{dev}===") 
        msg_processing_thread = threading.Thread(target=register_device,  args=(dev, database, dev_info,))
        msg_processing_thread.start()
        sleep(2)

def main():
    register_all_devices()

def register_device(dev_name, database, dev_info1):
    dev_info1.name = "ska000/spf/" + dev_name 
    dev_info1._class = "Spfc"
    dev_info1.server = "Spfc/4F1018"
    exception = True
    int_success_pause = 60
    while (exception):
        try:
            database.add_device(dev_info1)
            sleep(1)
            dp = DeviceProxy(dev_info1.name)
            print(dp.get_attribute_list())
        except Exception as ex:
            exception = True
            print(f"!!Reg. {dev_name} \n Exception occured:")
            print(ex)
            sleep(1)
            continue
        else:
            log_test.info(f"== {dev_name} registered ==")
            print(f"Now will pause for { int_success_pause } seconds")
            sleep(int_success_cause)
            exception = False
        sleep(1)

if __name__ == "__main__":
    main()