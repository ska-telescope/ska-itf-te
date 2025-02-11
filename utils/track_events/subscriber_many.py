""" Light Client"""
import logging
from os import getenv
from datetime import datetime
from time import localtime, strftime
import time
import tango
import sys
logger = logging.getLogger("event-subscriber")
callback_1_counter = 0
callback_3_counter = 0

def callback(event):
    """callback"""
    global callback_1_counter

    callback_1_counter = callback_1_counter + 1

    if callback_1_counter == 10:
        callback_1_counter = 0
        logger.info(f"{event}")
        print(f"{event}")
        pub_time = timeval_to_datetime(event.attr_value.time)
        reception_time = timeval_to_datetime(event.reception_date)
        print(f"Latency: {reception_time - pub_time}")
        callback_time = datetime.now()
        print(f"Callback - Reception: {callback_time - reception_time}")
    if event.err:
        sys.exit()

def callback_2(event):
    pass

def callback_3(event):
    global callback_3_counter

    callback_3_counter = callback_3_counter + 1
    if callback_3_counter == 10:
        callback_3_counter = 0
        print(f"{event}")
        pub_time = timeval_to_datetime(event.attr_value.time)
        reception_time = timeval_to_datetime(event.reception_date)
        print(f"Latency: {reception_time - pub_time}")
        callback_time = datetime.now()
        print(f"Callback - Reception: {callback_time - reception_time}")
    if event.err:
        sys.exit()

def timeval_to_datetime(time_val):
    sec = time_val.tv_sec
    nsec = time_val.tv_nsec
    usec = time_val.tv_usec
    time_datetime = datetime.fromtimestamp(sec+usec/1e6+nsec/1e9)
    return time_datetime

if __name__ == "__main__":
    attr_name = getenv("ATTR_NAME")
    try:
        attr_proxy = tango.AttributeProxy(attr_name)
        attr_2_proxy = tango.AttributeProxy("tango://tango-databaseds.integration-dish-lmc-ska001.svc.miditf.internal.skao.int:10000/mid-dish/ds-manager/ska001/achievedPointing")
        id = attr_proxy.subscribe_event(tango.EventType.CHANGE_EVENT, callback)
        id_2 = attr_2_proxy.subscribe_event(tango.EventType.CHANGE_EVENT, callback_3)
        for i in range(20000):
            id = attr_proxy.subscribe_event(tango.EventType.CHANGE_EVENT, callback_2)
    except Exception as e:
        logging.error(f"exception: {e}")
    while True:  # keep container running
        time.sleep(1)