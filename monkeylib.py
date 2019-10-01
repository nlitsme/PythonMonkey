from __future__ import print_function, division
"""
Provide an interface to the android 'monkey.jar' ui control interface.
"""
import socket
import time
import select
import re

"""
Commands implemented by the daemon running on the Android device.

wake
listvar
getvar <varname>
type  <string>
touch {down,up,move} <x> <y>
tap <x> <y>
press <keycode>          == key down + key up
key  {up,down} <keycode>

quit
deferreturn [event] [timeout (ms)] [command]
flip {open,close}
trackball <dx> <dy>
sleep  <msec>

listviews
queryview "viewid" <controlid> <command:gettext,getparent,...>
 ... commands: getlocation gettext getclass getchecked getenabled getselected
               setselected getfocused setfocused getparent getchildren getaccessibilityids

getrootview
getviewswithtext  "text"
"""


class Monkey:
    """
    Class managing a monkey connection.
    """
    def __init__(self, port):
        self.sock = socket.socket()
        self.sock.connect(("127.0.0.1", port))

    def send(self, cmd, timeout=0.5):
        self.sock.send((cmd + "\n").encode('utf-8'))
        res = self.readuntil(b"\n", timeout)
        if res:
            return res.decode('utf-8')

    def readuntil(self, char, timeout):
        self.sock.setblocking(0)
        buf = b''
        foundchar = False
        tstart = time.time()
        tend = tstart + timeout
        while time.time() < tend:
            ready = select.select([self.sock], [], [], 0.1)
            if ready[0]:
                c = self.sock.recv(1)
                if c == char:
                    foundchar = True
                    break
                buf += c
        self.sock.setblocking(1)
        if foundchar:
            return buf

    def keyevent(self, key):
        res = self.send("press %d" % key)
        return res == "OK"

    def sendtext(self, txt):
        res = self.send("type %s" % txt)
        return res == "OK"

    def wake(self):
        res = self.send("wake", 1.0)
        return res == "OK"

    def drag(self, frm, to, duration, steps):
        """
                   #0        #1         #(steps-1)
        ---  down <dt> move <dt> move ... <dt> move <dt> up
        t:    t0                                         t0+dur
        x:    x0       x0+dx                    x1       x1
        """
        dx = (to[0]-frm[0]) / steps
        dy = (to[1]-frm[1]) / steps

        dt = duration / (steps+1)

        tstart = time.time()
        tend = tstart + duration

        pos = frm
        self.touch("down", pos)

        for _ in range(steps):
            time.sleep(dt)

            pos = (pos[0]+ dx, pos[1] + dy)

            self.touch("move", pos)

        time.sleep(dt)
        self.touch("up", to)

    def touch(self, how, pos):
        res = self.send("touch %s %d %d" % (how, pos[0], pos[1]))
        return res == "OK"

    def tap(self, pos):
        res = self.send("tap %d %d" % (pos[0], pos[1]))
        return res == "OK"

    def listvar(self):
        response = self.send("listvar")
        if not response.startswith('OK:'):
            return
        return response[3:].split(" ")

    def getvar(self, name):
        response = self.send("getvar %s" % name)
        if not response.startswith('OK:'):
            # .. maybe raise exception with error msg ..
            return
        return response[3:]

    @staticmethod
    def launchmonkey(adb):
        """
        returns a Monkey object
        """
        print("fwd->", adb.forward(12345, 12345))

        # or 'toybox killall'
        killres = adb.shell("killall com.android.commands.monkey")
        if killres.find("killall: not found") >= 0:
            pidline = adb.shell("ps | grep commands.monkey")
            if pidline:
                m = re.match(r'^\w+\s+(\d+)', pidline)
                if m:
                    pid = int(m.group(1))
                    killres = adb.shell("kill %d" % pid)
            else:
                killres = 'process not found'
        print("kill->", killres)
        time.sleep(0.1)
        monkeycmd = adb.makeshell("monkey -v --script-log --port 12345")

        if not Monkey.wait_for_monkey(monkeycmd):
            print("Failed to start monkey")
            return
        print("monkey active")

        for _ in range(4):
            mon = Monkey(12345)
            try:
                if mon.wake():
                    break
            except Exception as e:
                print("trying -> %s" % e)
                import traceback
                traceback.print_exc()

            mon = None
            time.sleep(0.5)

        if not mon:
            print("could not connect to Monkey")
            return

        monkeycmd.close()

        return mon

    @staticmethod
    def wait_for_monkey(monkeycmd):
        """
        wait until the monkey tool has launched without an error.
        """
        tstart = time.time()
        tend = tstart + 10.0

        print("=== waiting for monkey")
        while time.time() < tend:
            resp = monkeycmd.read()
            if resp:
                print("monkeycmd -> ", resp)
                if resp.find('Error') >= 0:
                    return
                if resp.find(":Monkey:")>=0:
                    print()
                    return True

            time.sleep(0.5)
        print()



