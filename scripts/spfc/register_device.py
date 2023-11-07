import argparse
import configparser
import subprocess
import tango
from time import sleep
from tango import Database, DbDevInfo,DeviceProxy
class RegisterSPFC:
    __database = None
    __dev_info = None
    __dev_proxy = None
    __server_location = ""
    __serial_number = ""
    __dict_device_names = dict([ ("spfc", "Spfc"), ("spf1", "Spf1"), ("spf2", "Spf2"),
                                 ("spf345", "Spf345"), ("spfhe","SpfHe"), ("spfvac","SpfVac")])
        
    def register_all_devices(self,tango_host, server_location, serial_number):
        self.__server_location = server_location
        self.__serial_number = serial_number
        tango_db_env = str(tango_host)
        tango_db_ip = str(tango_db_env.split(":")[0])
        tango_db_port = int(tango_db_env.split(":")[1])
        self.__database = Database(tango_db_ip, tango_db_port)
        self.__dev_info = DbDevInfo()

        for (dev_name,class_name) in self.__dict_device_names.items():
            dev_class = str(dev_name[0].upper()) + str(dev_name[1:])
            self.__dev_info.name = self.__server_location + "/spf/" + dev_name
            self.__dev_info._class = class_name
            self.__dev_info.server = class_name + "/" + self.__serial_number            
            target=self.register_device()
            sleep(5)
        #All TDS's are registered. Add their properties
        self.apply_device_properties()
    
    def apply_device_properties(self):
        #Devices are registered now we add their properties
        print("Adding device properties...")
        for (dev_name, class_name) in self.__dict_device_names.items():
            self.__add_device_properties(dev_name)
            sleep(5)

    def __add_device_properties(self, dev_name):
        match dev_name:
            case "spfc":
                ls_properties = {"SpfHeLocation":[self.__server_location+"/spf/spfhe"], "SpfVacLocation":[self.__server_location+"/spf/spfvac"],
                                "Spf1Location":[self.__server_location+"/spf/spf1"], "Spf2Location":[self.__server_location+"/spf/spf2"],
                                "Spf345Location":[self.__server_location+"/spf/spf345"]}
            case "spf1":
                ls_properties = {"ttyPort":["/dev/ttyS1"]}

            case "spf2":
                ls_properties = {"ttyPort":["/dev/ttyS2"], "SpfHeLocation":[self.__server_location+"/spf/spfhe"],
                                "SpfVacLocation":[self.__server_location+"/spf/spfvac"]}

            case "spf345":
                ls_properties = {"ttyPort":["/dev/ttyS3"], "SpfHeLocation":[self.__server_location+"/spf/spfhe"], 
                                 "SpfVacLocation":[self.__server_location+"/spf/spfvac"]}

            case _:
                print(f"Leaving out {dev_name}'s properties.")
                return
        print(f"Adding {dev_name}'s propeties...")
        self.__database.put_device_property(self.__server_location + "/spf/" + dev_name, ls_properties)


    def register_device(self):
        exception = True
        int_success_pause = 60
        try:
            self.__database.add_device(self.__dev_info)
            sleep(1)
            self.__dev_proxy = DeviceProxy(self.__dev_info.name)
            print(f"server========={self.__dev_info.server}==========")
            print(f"class={self.__dev_info._class}")
            print(f"server={self.__dev_info.server}\n\n")
            print(self.__dev_proxy.get_attribute_list())
        except Exception as ex:
            exception = True
            print(f"!!Reg. {self.__dev_info.name} \n Exception occured:")
            print(ex)
            sleep(2)
        sleep(5)

def main():
    reg_spfc = RegisterSPFC()
    pars = argparse.ArgumentParser()
    pars.add_argument("tango_host", help="Tango host of the tango database and port. For example 10.1.2.4:10000", type=str)
    pars.add_argument("dev_location", help="Device server location, for example ska001", type=str)
    pars.add_argument("spfc_host", help="SPFC IP address, for example 10.165.3.33", type=str)
    tango_host = pars.parse_args().tango_host
    device_location = pars.parse_args().dev_location
    spfc_host = pars.parse_args().dev_location
    spfc_config = configparser.ConfigParser()
    spfc_config.read("resources/spfc/spfc_config.ini")
    spfc_serial_number = spfc_config['Serial_Nr']['SPFC']
    print(f"tango_host={tango_host}")
    print(f"device_location={device_location}")
    print(f"serial_num={spfc_serial_number}")
    print(f"spfc_host={spfc_host}")
    reg_spfc.register_all_devices(tango_host, device_location, spfc_serial_number)

    #Restart SPFC
    spfc_response = subprocess.call(["ssh", f"skao@{spfc_host}", "-t", '"sudo /bin/systemctl restart spfc-system.target"'] ,stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    print(f"spfc_response={spfc_response}")

if __name__ == "__main__":
    main()