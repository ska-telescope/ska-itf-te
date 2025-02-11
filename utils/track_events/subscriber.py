""" Light Client"""
import logging
from os import getenv
from datetime import datetime
import time
import tango
logger = logging.getLogger("event-subscriber")

def callback(event):
    """callback"""
    logger.info(f"{event}")
    print(f"{event}")
    pub_time = timeval_to_datetime(event.attr_value.time)
    reception_time = timeval_to_datetime(event.reception_date)
    print(f"Latency: {reception_time - pub_time}")

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
        id = attr_proxy.subscribe_event(tango.EventType.CHANGE_EVENT, callback)
    except Exception as e:
        logging.error(f"exception: {e}")
    while True:  # keep container running
        time.sleep(1)