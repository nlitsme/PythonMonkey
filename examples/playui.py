from __future__ import print_function, division
"""
"""
import time
import datetime
from adblib import ADB
from monkeylib import Monkey
from collections import defaultdict


class DeviceInteraction:
    def __init__(self):
        self.adb = None
        self.mon = None

    def connect(self, pin):
        self.adb = ADB()
        self.adb.connect()
        self.mon = Monkey.launchmonkey(self.adb)
        return self.unlockphone(pin)


    def unlockphone(self, pin):
        screenstate = self.adb.devicestate()
        print("screen='%s'" % screenstate)

        if not screenstate:
            print("error getting devstate")
            return

        if screenstate == 'ON_UNLOCKED':
            print("already unlocked : '%s'" % screenstate)
            return True

        if screenstate == 'OFF':
            print("turning on screen")
            self.mon.keyevent(26)   # screen on
            time.sleep(1.0)   # NOTE: need much longer here on android6 than on android9
        self.mon.keyevent(82)   # unlock
        time.sleep(0.5)
        if pin:
            print("entering pin")
            self.mon.sendtext(pin)
            time.sleep(0.1)
            self.mon.keyevent(66)   # enter pin

        time.sleep(1.0)   # NOTE: need much longer here on android6 than on android9
        screenstate = self.adb.devicestate()
        print("pin -> screen='%s'" % screenstate)

        return screenstate == 'ON_UNLOCKED'


def main():
    dev = DeviceInteraction()
    if not dev.connect("0000"):
        print("failed to unlock")
        return


if __name__=='__main__':
    main()
