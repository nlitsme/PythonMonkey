from __future__ import print_function, division
"""
See the adb/SERVICES.TXT file for what commands adb supports.
"""
import PIL.Image
import struct
import socket
import re
import select


class ADBConnection:
    """
    Connect to local adb server instance.

    provides the following methods:

    `send` - sends a length prefixed command to the adb instance.
    `recv` - receives a length prefixed response from the adb instance.

    `write` - sends raw data
    `read` - reads raw data

    `readavailable` - reads all currently available data.

    """
    def __init__(self):
        self.sock = socket.socket()
        self.sock.connect(("127.0.0.1", 5037))

    def close(self):
        self.sock.close()

    def send(self, cmd):
        self.sock.send(b"%04x" % len(cmd) + cmd.encode('utf-8'))

        resp = self.sock.recv(4)
        if resp != b'OKAY':
            raise Exception("ADB:%s" % resp)

    def recv(self):
        resplen = self.sock.recv(4).decode('utf-8')
        resplen = int(resplen, 16)

        return self.sock.recv(resplen).decode('utf-8')

    def write(self, data):
        self.sock.send(data)

    def read(self, n):
        return self.sock.recv(n)

    def readavailable(self):
        self.sock.setblocking(0)
        timeout_in_seconds = 0.5
        ready = select.select([self.sock], [], [], timeout_in_seconds)
        data = None
        if ready[0]:
            data = self.sock.recv(1024*1024)
        self.sock.setblocking(1)
        return data


class ADBFrameCapture:
    """
    Frame Capture object.
    v2 servers support delayed capture: the object can be initialized,
    and the capture executed at a later moment by transmitting one byte.

    The capture method returns a PIL Image object.
    """
    def __init__(self, adb):
        self.conn = None

        self.connect(adb.serialnr)

    def connect(self, serialnr):
        self.conn = ADBConnection()
        self.conn.send("host:transport:%s" % serialnr)
        self.conn.send("framebuffer:")
        (
            self.version,       # '2'
            bpp ,          # bits per pixel
        ) = struct.unpack("<LL", self.conn.read(8))
        if self.version == 2:
            colorSpace, = struct.unpack("<L", self.conn.read(4))
        hdr = self.conn.read(44)
        (
            self.size,     # in bytes
            self.width,    # in pixels
            self.height,   # in pixels
            red_offset,    # in bits
            red_length,    # in bits
            blue_offset,   # in bits
            blue_length,   # in bits
            green_offset,  # in bits
            green_length,  # in bits
            alpha_offset,  # in bits
            alpha_length,  # in bits
        ) = struct.unpack("<11L", hdr)

        params = (bpp, red_offset,   red_length,   blue_offset,  blue_length,  green_offset, green_length, alpha_offset, alpha_length)

        if params == ( 32, 0, 8, 16, 8, 8, 8, 24, 8):   self.mode, self.rawmode = "RGBA", "RGBA"  # RGBA_8888
        elif params == ( 32, 0, 8, 16, 8, 8, 8, 24, 0): self.mode, self.rawmode = "RGB", "RGBX"   # RGBX_8888
        elif params == ( 24, 0, 8, 16, 8, 8, 8, 24, 0): self.mode, self.rawmode = "RGB", "RGB"    # RGB_888
        elif params == ( 16, 11, 5, 0, 5, 5, 6,  0, 0): self.mode, self.rawmode = "RGB", "RGB;16" # RGB_565
        elif params == ( 32, 16, 8, 0, 8, 8, 8, 24, 8): self.mode, self.rawmode = "RGBA", "BGRA"  # BGRA_8888
        else:
            raise Exception("unsupported pixel format")

    def capture(self):
        if self.version == 2:
            self.conn.write(b'\x00')
        imgdata = b''
        try:
            while len(imgdata) < self.size:
                want = min(self.size-len(imgdata), 1024*1024)
                data = self.conn.read(want)
                if data is None:
                    break

                imgdata += data
        except Exception as e:
            print("ERROR %s" % e)

        return PIL.Image.frombytes(self.mode, (self.width, self.height), imgdata, "raw", self.rawmode)


class ADBShell:
    """
    Starts an adb shell connection.
    """
    def __init__(self, adb, cmd):
        self.conn = ADBConnection()
        self.conn.send("host:transport:%s" % adb.serialnr)
        self.conn.send("shell:%s" % cmd)
        #response = conn.read()
        #return response.decode('utf-8')

    def close(self):
        self.conn.close()

    def read(self):
        return self.conn.readavailable()

    def write(self, cmd):
        return self.conn.send(cmd)


class ADB:
    """
    Object for managing an adb connection to a specific device.
    """
    def __init__(self):
        self.serialnr = None

    def version(self):
        conn = ADBConnection()
        conn.send("host:version")
        return conn.recv()

    def devices(self):
        """
        yields pairs of : serialnr, device-state
        """
        conn = ADBConnection()
        conn.send("host:track-devices")
        response = conn.recv()

        for line in response.rstrip("\n").split("\n"):
            m = re.match(r'^(\S+)\s+(\w+)', line)
            if m:
                yield m.group(1), m.group(2)

    def shell(self, cmd):
        if not self.serialnr:
            raise Exception("must set serialnr")
        conn = ADBConnection()
        conn.send("host:transport:%s" % self.serialnr)
        conn.send("shell:%s" % cmd)
        #response = conn.read()
        #return response.decode('utf-8')

    def forward(self, local, remote):
        conn = ADBConnection()
        conn.send("host-serial:%s:forward:tcp:%d;tcp:%d" % (self.serialnr, local, remote))

    def makecapture(self):
        return ADBFrameCapture(self)

    def makeshell(self, cmd):
        return ADBShell(self, cmd)

    def takeSnapshot(self):
        cap = self.makecapture()
        return cap.capture()

