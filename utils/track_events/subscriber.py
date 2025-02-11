""" Light Client"""
import logging
from os import getenv
import time
import tango
logger = logging.getLogger("event-subscriber")

def callback(event):
    """callback"""
    logger.info(f"{event}")

if __name__ == "__main__":
    attr_name = getenv("ATTR_NAME")
    try:
        attr_proxy = tango.AttributeProxy(attr_name)
        id = attr_proxy.subscribe_event(tango.EventType.CHANGE_EVENT, callback)
    except Exception as e:
        logging.error(f"exception: {e}")
    while True:  # keep container running
        time.sleep(1)