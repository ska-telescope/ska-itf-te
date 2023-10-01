dev_info1 = DbDevInfo()
from tango import (
    StdStringVector,
    Database,
    DbDatum,
    DbData,
    DbDevInfo,
    DbDevInfos,
    DbDevImportInfo,
    DbDevExportInfo,
    DbDevExportInfos,
    DbHistory,
    DbServerInfo,
    DbServerData,
)

def main():
    dev_info1.name = 'mid-itf/SPFC/1'
    dev_info1._class = 'SPFC'
    dev_info1.server = 'SPFC/test'
    db = Database("10.164.10.22", 10000)
    db.add_server(dev_info1.server, dev_info1, with_dserver=True)
    dev_info = db.get_device_info(dev_info1.name)
    print("Registered device=" + str(dev_info))

if __name__ == "__main__":
    main()