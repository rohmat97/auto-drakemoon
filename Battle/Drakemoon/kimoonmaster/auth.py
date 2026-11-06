# auth.py

import sys
import uuid
import hashlib
import wmi
from tkinter import messagebox
from config import AUTHORIZED_HARDWARE_ID

def get_composite_hardware_id():
    c = wmi.WMI()
    disk_serial = c.Win32_DiskDrive()[0].SerialNumber.strip() if c.Win32_DiskDrive() else 'unknown'
    mac = ':'.join(['{:02x}'.format(uuid.getnode() >> i & 255) for i in range(0, 48, 8)][::-1])
    composite = f"{disk_serial}-{mac}"
    return hashlib.sha256(composite.encode()).hexdigest()

def check_hardware_authorization():
    current_id = get_composite_hardware_id()
    if current_id != AUTHORIZED_HARDWARE_ID:
        messagebox.showerror('Error', f'Unauthorized device!\nYour hardware ID: {current_id}\nPlease contact the admin for authorization.')
        sys.exit(1)
