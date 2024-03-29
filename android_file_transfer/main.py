"""Copy KMZ files onto Android device, in the correct directory."""

from pathlib import Path
from uuid import uuid4

from pymtp import get_devices, MTPDevice


unique_id = str(uuid4()).upper()

    
devices = get_devices()
# Assumes only one device is connected
device = devices[0]
print(device)

# TODO example https://github.com/emdete/python-mtp/blob/master/examples/sendfile.py
# TODO or use https://github.com/hanwen/go-mtpfs to mount first

# # Connect to the device
# with MTPDevice(device.device_entry) as mtp:
#     # List the directories on the device
#     dirs = mtp.get_folder_list()
