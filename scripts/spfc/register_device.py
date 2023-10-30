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
    for dev_name in ls_device_names:
        dev_class = str(dev_name[0].upper()) + str(dev_name[1:])
        dev_info.name = "ska000/spf/" + dev_name 
        dev_info._class = dev_class
        dev_info.server = dev_class + "/4F1018"      
        register_device(dev_info, database)
        sleep(2)

def main():
    register_all_devices()

def register_device(dev_info, database):
    exception = True
    int_success_pause = 60
    while (exception):
        sleep(1)
        try:
            database.add_device(dev_info)
            dp = DeviceProxy(dev_info.name)
            print(dp.get_attribute_list())
        except Exception as ex:
            exception = True
            print(f"!!Registering name={dev_info.name} \n Exception occured!!")
            print(ex)
            pass
        else:
            log_test.info(f"== {dev_info.name} registered ==")
            exception = False

if __name__ == "__main__":
    main()