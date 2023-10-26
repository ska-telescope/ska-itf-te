import os
import subprocess
import sys
import tango
from time import sleep
from tango import Database, DbDevInfo,DeviceProxy
import threading

def register_device():
        msg_processing_thread = threading.Thread(target=self.process_send_msg_queue, daemon=True)
        msg_processing_thread.start()
def main():
    dev_info1 = DbDevInfo()
    tango_db_env = str(tango.ApiUtil.get_env_var("TANGO_HOST"))
    print(tango_db_env)
    tango_db_ip = str(tango_db_env.split(":")[0])
    tango_db_port = int(tango_db_env.split(":")[1])
    dev_info1.name = sys.argv[1]
    dev_info1._class = sys.argv[2]
    dev_info1.server = sys.argv[3]
    database = Database(tango_db_ip, tango_db_port)
    exception = True
    int_success_cause = 60
    while (True):
        try:
            database.add_device(dev_info1)
            sleep(2)
            dp = DeviceProxy(dev_info1.name)
            print(dp.get_attribute_list())
        except Exception as ex:
            exception = True
            print("Exception occured:")
            print(ex)
            continue
        else:
            print("Registration succeded.")
            print(f"Now will pause for { int_success_cause } seconds")
            sleep(int_success_cause)
            exception = False
        sleep(2)

if __name__ == "__main__":
    main()