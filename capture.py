"""
Script to take a screen capture from the attached android device
using the `adb` `framebuffer` function.
"""
from adblib import ADB
from monkeylib import Monkey

def start():
    import sys
    fn = sys.argv[1]

    adb = ADB()
    print("adb version = %s" % adb.version())
    for serial, state in adb.devices():
        adb.serialnr = serial

    cap = adb.makecapture()
    img = cap.capture()
    img.save(fn)


if __name__=='__main__':
    start()
