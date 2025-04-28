echo "Testing connecting to Tango Device:"
# python3 -c "from tango import DeviceProxy; DeviceProxy('tango://10.164.5.16:10000/mid-dish/dish-manager/ska036').ping()"

# telnet tango-databaseds.dish-lmc-ska036.svc.ska036.miditf.internal.skao.int 10000
python3 -c "from tango import DeviceProxy; print(DeviceProxy('tango-databaseds.dish-lmc-ska036.svc.ska036.miditf.internal.skao.int:10000/mid-dish/dish-manager/ska036').ping())"
