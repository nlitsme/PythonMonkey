from __future__ import print_function, division
"""
Provide an interface to the android 'monkey.jar' ui control interface.
"""
import socket
import time
import select
"""
Commands implemented by the daemon running on the Android device.

wake
type  <string>
touch {down,up,move} <x> <y>
tap <x> <y>
press <keycode>          == key down + key up
quit
deferreturn [event] [timeout (ms)] [command]
flip {open,close}
trackball <dx> <dy>
key  {up,down} <keycode>
sleep  <msec>
listvar
getvar <varname>

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
        return self.readuntil(b"\n", timeout)

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

    def wake(self):
        self.send("wake")

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
        self.send("touch %s %d %d" % (how, pos[0], pos[1]))

    def tap(self, pos):
        self.touch("down", pos)
        time.sleep(0.05)
        self.touch("up", pos)

