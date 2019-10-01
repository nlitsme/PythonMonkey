from __future__ import print_function, division
"""
See the adb/SERVICES.TXT file for what commands adb supports.
"""
import PIL.Image
import struct
import socket
import re
import select
import os
import time

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
    def __init__(self, conn):
        self.conn = conn

        self.connect()

    def connect(self):
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
    def __init__(self, conn, cmd):
        self.conn = conn
        self.conn.send("shell:%s" % cmd)
        #response = conn.read()
        #return response.decode('utf-8')

    def close(self):
        self.conn.close()

    def read(self):
        res = self.conn.readavailable()
        if res:
            return res.decode('utf-8')

    def write(self, cmd):
        return self.conn.send(cmd)

class ADBSync:
    """
    Use adb to transfer to and from the device.
    """
    def __init__(self, conn, usev2):
        self.usev2 = usev2

        self.conn = conn
        self.conn.send("sync:")

    def stat(self, fname):
        fname = fname.encode('utf-8')
        
        self.conn.write(struct.pack("<4sL", b"STA2" if self.usev2 else b"STAT", len(fname)) + fname)
        response = self.conn.read(72 if self.usev2 else 16)

        if self.usev2:
            (
            magic, err, dev, ino, mode, nlink, uid, gid, size, atime, mtime, ctime 
            ) = struct.unpack("<4s9L4Q", response)
            if magic != b'STA2':
                raise Exception("expected STA2 answer")
        else:
            magic, mode, size, mtime = struct.unpack("<4s3L", response)
            if magic != b'STAT':
                raise Exception("expected STAT answer")

        return mode, size, mtime

    def get(self, fname):
        """
        downloads / pulls a file from the device.
        """
        fname = fname.encode('utf-8')
        self.conn.write(struct.pack("<4sL", b"RECV", len(fname)) + fname)

        while True:
            response = self.conn.read(8)
            magic, datasize = struct.unpack("<4sL", response)
            if magic == b'DONE':
                break
            if magic == b'FAIL':
                errmsg = self.conn.read(datasize)
                raise Exception("file error: %s" % errmsg.decode('utf-8'))
            if magic != b"DATA":
                print("m=%s" % magic)
                raise Exception("expected DATA answer")

            received = 0
            while received < datasize:
                data = self.conn.read(min(65536, datasize-received))
                yield data
                received += len(data)

    def put(self, fname, fh):
        """
        uploads / pushes file to the device.
        """
        fname = fname.encode('utf-8')
        self.conn.write(struct.pack("<4sL", b"SEND", len(fname)) + fname)
        
        while True:
            data = fh.read(65536)
            if not data:
                break
            self.conn.write(struct.pack("<4sL", b"DATA", len(data)))
            self.conn.write(data)

        self.conn.write(struct.pack("<4sL", b"DONE", int(time.time())))

    def list(self, path):
        """
        yields a directory list
        """
        path = path.encode('utf-8')
        self.conn.write(struct.pack("<4sL", b"LIST", len(path)) + path)

        while True:
            hdr = self.conn.read(20)
            magic, mode, size, time, nlen = struct.unpack("<4s4L", hdr)
            if magic == b'DONE':
                break
            if magic != b'DENT':
                raise Exception("expected DENT or DONE header")
            name = self.conn.read(nlen)

            yield mode, size, time, name.decode('utf-8')

class ADB:
    """
    Object for managing an adb connection to a specific device.
    """
    def __init__(self):
        self.serialnr = None

    def maketransport(self):
        conn = ADBConnection()
        if self.serialnr:
            conn.send("host:transport:%s" % self.serialnr)
        else:
            conn.send("host:transport-any")
        return conn

    def makecapture(self):
        """
        Create a screencapture object.
        """
        return ADBFrameCapture(self.maketransport())
    def makeshell(self, cmd):
        """
        Create an interactive command shell object.
        """
        return ADBShell(self.maketransport(), cmd)
    def makesync(self, v2):
        """
        Create a file sync object.
        """
        return ADBSync(self.maketransport(), v2)


    def version(self):
        """
        Requests the adb version, and optionally launches the adb server.
        """
        for _ in range(2):
            try:
                conn = ADBConnection()
                conn.send("host:version")
                return conn.recv()
            except:
                if _ > 0:
                    raise

                # retry after starting server
                os.system("adb start-server")

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
        """
        execute a shell command on the device.
        """
        sh = self.makeshell(cmd)
        time.sleep(0.1)
        return sh.read()

    def forward(self, local, remote):
        """
        forward a local port to a device port
        """
        conn = ADBConnection()
        conn.send("host-serial:%s:forward:tcp:%d;tcp:%d" % (self.serialnr, local, remote))

    def getfeatures(self):
        """
        return a list of features.
        """
        conn = ADBConnection()
        conn.send("host-serial:%s:features" % (self.serialnr))

        return conn.recv().split(",")

    def reboot(self, into=None):
        """
        reboot the device in the specified mode.
        """
        conn = self.maketransport()
        conn.send("reboot:%s" % (into or ""))

    def remount(self, args=None):
        """
        remount system partition read-write
        """
        conn = self.maketransport()
        conn.send("remount:%s" % (args or ""))

    def root(self):
        """
        Restart adb as root
        """
        conn = self.maketransport()
        conn.send("root:")

    def takeSnapshot(self):
        cap = self.makecapture()
        return cap.capture()

    def connect(self):
        print("adb version = %s" % self.version())
        for serial, state in self.devices():
            self.serialnr = serial


    def devicestate(self):
        sh = self.makeshell("dumpsys nfc")
        time.sleep(0.2)
        output = sh.read()
        if not output:
            return False, False, False

        i = output.find('mScreenState=')
        if i==-1:
            return
        e = output.find('\n', i)
        state = output[i+13:e].rstrip('\r')

        return state


def main():
    adb = ADB()

    adbsync = adb.makesync(True)

    for ent in adbsync.list("/"):
        print("%08x %08x %08x %s" % ent)

    for fn in ("/init.rc", "/verity_key", "/", "/sdcard", "/sepolicy"):
        try:
            print("==>", fn, "<==")
            for data in adbsync.get(fn):
                print("%8d bytes" % len(data))
        except Exception as e:
            print("- %s" % e)

    with open("bb-packettrace.txt", "rb") as fh:
        adbsync.put("/sdcard/tstdata.dat", fh)


if __name__=='__main__':
    main()

