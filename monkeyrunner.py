"""
Module implementing the Android monkeyrunner api.
The interface exported by this module is exactly the api described here:

    https://developer.android.com/studio/test/monkeyrunner

This is implemented by using two lower level modules, monkeylib and adblib,
which connect to respectively monkey.jar and the ADB Daemon.

"""
import time
import re
from adblib import ADB
from monkeylib import Monkey


def center(msg, width):
    border = width - len(msg)
    left = border // 2
    right = border - left
    return  " " * left + msg + " " * right

def quotespaces(x):
    if x.find(' '):
        return "\"%s\"" % x
    return x


class MonkeyRunner:
    """
    Main entry point for MonkeyRunner

    This class has only static methods.
    """
    @staticmethod
    def alert(message, title = "Alert", okTitle = "OK"):
        """
        Display an alert dialog to the process running the current script.  The dialog 
        is modal, so the script stops until the user dismisses the dialog.

          Args:
            message - The message to display in the dialog.
            title - The dialog's title. The default value is 'Alert'.
            okTitle - The text to use in the dialog button. The default value is 'OK'.
        """
        m = max(len(message), 6 + len(title))
        print("*" * (m + 4))
        print("***", center(title, m-6), "***")
        print("*", center(message, m), "*")
        print("*" * (m + 4))
        input(okTitle + " (Press Enter)")

    @staticmethod
    def choice(message, choices, title = "Input"):
        """
        Display a choice dialog that allows the user to select a single item from a 
        list of items.

          Args:
            message - The prompt message to display in the dialog.
            choices - An iterable Python type containing a list of choices to display
            title - The dialog's title. The default is 'Input'
        """
        m = max(len(message), 6 + len(title))
        print("*" * (m + 4))
        print("***", center(title, m-6), "***")
        print("*", center(message, m), "*")
        print("*" * (m + 4))
        for i, choice in enumerate(choices):
            print("  %2d) %s" % (i, choice))
        while True:
            r = input(okTitle + " (type choice, Enter for cancel)")
            if r in ("", "\n"):
                return -1
            try:
                r = int(r)
                if 0 <= r < len(choices):
                    return r
            except:
                import traceback
                traceback.print_exc()
                pass
            print("invalid choice - %s" % r)

    @staticmethod
    def help(format = "text"):
        """
        Format and display the API reference for MonkeyRunner.

          Args:
            format - The desired format for the output, either 'text' for plain text 
                     or 'html' for HTML markup.
        """
        # todo - see monkeyhelp.py

    @staticmethod
    def input(message, initialValue = "", title = "Input", okTitle=None, cancelTitle=None):
        """
        Display a dialog that accepts input. The dialog is ,modal, so the script stops 
        until the user clicks one of the two dialog buttons. To enter a value, the 
        user enters the value and clicks the 'OK' button. To quit the dialog without 
        entering a value, the user clicks the 'Cancel' button. Use the supplied 
        arguments for this method to customize the text for these buttons.

          Args:
            message - The prompt message to display in the dialog.
            initialValue - The initial value to supply to the user. The default is an 
                           empty string)
            title - The dialog's title. The default is 'Input'
            okTitle - The text to use in the dialog's confirmation button. The default 
                      is 'OK'.The text to use in the dialog's 'cancel' button. The 
                      default is 'Cancel'.
            cancelTitle
        """
        # NOTE: okTitle & cancelTitle seem to be unused.
        m = max(len(message), 6 + len(title))
        print("*" * (m + 4))
        print("***", center(title, m-6), "***")
        print("*", center(message, m), "*")
        print("*" * (m + 4))
        readline.insert_text(initialValue)
        return input("--> ")

    @staticmethod
    def loadImageFromFile(path):
        """
        Loads a MonkeyImage from a file.

          Args:
            path - The path to the file to load.  This file path is in terms of the 
                   computer running MonkeyRunner and not a path on the Android Device. 
        """
        return MonkeyImage(PIL.load(path))

    @staticmethod
    def sleep(seconds):
        """
        Pause the currently running program for the specified number of seconds.

          Args:
            seconds - The number of seconds to pause.
        """
        time.sleep(seconds)


    @staticmethod
    def waitForConnection(timeout, deviceId = ".*"):
        """
        Waits for the workstation to connect to the device.

          Args:
            timeout - The timeout in seconds to wait. The default is to wait 
                      indefinitely.
            deviceId - A regular expression that specifies the device name. See the 
                       documentation for 'adb' in the Developer Guide to learn more 
                       about device names.
        """
        if timeout:
            tstart = time.time()
            tend = tstart + timeout

        adb = ADB()
        print("adb version = %s" % adb.version())
        while not timeout or time.time() < tend:
            for devid, state in adb.devices():
                if state == 'device' and re.match(deviceId, devid):
                    adb.serialnr = devid
                    mlib = Monkey.launchmonkey(adb)

                    if mlib:
                        return MonkeyDevice(adb, mlib)
            time.sleep(0.2)

# -- end of MonkeyRunner --

class MonkeyDevice:
    """
    Represents a device attached to the system.

    Class Fields: 
      DOWN - Sends a DOWN event when used with touch() or press().
      UP - Sends an UP event when used with touch() or press().
      DOWN_AND_UP - Sends a DOWN event, immediately followed by an UP event when 
                    used with touch() or press()
      MOVE - Sends a MOVE event when used with touch().
    """


    DOWN = "down"
    DOWN_AND_UP = "downAndUp"
    MOVE = "move"
    UP = "up"

    def __init__(self, adb, mlib):
        self.adb = adb
        self.mlib = mlib

    def broadcastIntent(self, uri=None, action=None, data=None, mimetype=None, categories=None, extras=None, component=None, flags=0):
        """
        Sends a broadcast intent to the device.

          Args:
            uri - The URI for the Intent.
            action - The action for the Intent.
            data - The data URI for the Intent
            mimetype - The mime type for the Intent.
            categories - An iterable of category names for the Intent.
            extras - A dictionary of extras to add to the Intent. Types of these 
                     extras are inferred from the python types of the values.
            component - The component of the Intent.
            flags - An iterable of flags for the Intent.All arguments are optional. 
                    The default value for each argument is null.(see android.content.
                    Context.sendBroadcast(Intent))
        """
        self.adb.shell("am broadcast " + self.makeargs(uri, action, data, mimetype, categories, extras, component, flags))

    def startActivity(self, uri=None, action=None, data=None, mimetype=None, categories=None, extras=None, component=None, flags=0):
        """
        Starts an Activity on the device by sending an Intent constructed from the 
        specified parameters.

          Args:
            uri - The URI for the Intent.
            action - The action for the Intent.
            data - The data URI for the Intent
            mimetype - The mime type for the Intent.
            categories - A Python iterable containing the category names for the 
                         Intent.
            extras - A dictionary of extras to add to the Intent. Types of these 
                     extras are inferred from the python types of the values.
            component - The component of the Intent.
            flags - An iterable of flags for the Intent.All arguments are optional. 
                    The default value for each argument is null.(see android.content.
                    Intent)
        """
        self.adb.shell("am start " + self.makeargs(uri, action, data, mimetype, categories, extras, component, flags))

    def makeargs(self, uri=None, action=None, data=None, mimetype=None, categories=None, extras=None, component=None, flags=0):
        args = []
        if action:
            args += ["-a", action]
        if data:
            args += ["-d", data]
        if mimetype:
            args += ["-t", mimetype]
        if extras:
            for key, item in extras:
                if type(item) == int:
                    argtype = "--ei"
                elif type(item) == bool:
                    argtype = "--ei"
                else:
                    argtype = "--es"
                args += [argtype, key, str(item)]
        if component:
            args += ["-n", component]
        if flags:
            args += ["-f", str(flags)]
        if uri:
            args += [uri]

        return " ".join(quotespaces(_) for _ in args)

    def drag(self, start, end, duration=1.0, steps=10):
        """
        Simulates dragging (touch, hold, and move) on the device screen.

          Args:
            start - The starting point for the drag (a tuple (x,y) in pixels)
            end - The end point for the drag (a tuple (x,y) in pixels)
            duration - Duration of the drag in seconds (default is 1.0 seconds)
            steps - The number of steps to take when interpolating points. (default is 
                    10)
        """
        self.mlib.drag(start, end, duration, steps)

    def getHierarchyViewer(self):
        """
        Get the HierarchyViewer object for the device.
        """
        # todo

    def getProperty(self, key):
        """
        Given the name of a variable on the device, returns the variable's value

          Args:
            key - The name of the variable. The available names are listed in
                  http://developer.android.com/guide/topics/testing/monkeyrunner.html.
        """
        return self.mlib.getvar(key)

    def getPropertyList(self):
        """
        Retrieve the properties that can be queried
        """
        return self.mlib.listvar()

    def getRootView(self):
        """
        Obtains current root view
        """
        # todo

    def getSystemProperty(self, key):
        """
        Synonym for getProperty()

          Args:
            key - The name of the system variable.
        """
        self.getProperty(key)

    def getViewByAccessibilityIds(self, windowId, accessibilityId ):
        """
        Obtains the view with the specified accessibility ids.

          Args:
            windowId - The window id of the view to retrieve.
            accessibilityId - The accessibility id of the view to retrieve.
        """
        # todo

    def getViewById(self, id):
        """
        Obtains the view with the specified id.

          Args:
            id - The id of the view to retrieve.
        """
        # todo

    def getViewIdList(self):
        """
        Retrieve the view ids for the current application
        """
        # todo

    def getViewsByText(self, text):
        """
        Obtains a list of views that contain the specified text.

          Args:
            text - The text to search for
        """
        # todo

    def installPackage(self, path):
        """
        Installs the specified Android package (.apk file) onto the device. If the 
        package already exists on the device, it is replaced.

          Args:
            path - The package's path and filename on the host filesystem.
        """

        remotename = self.adb.shell("mktemp") + ".apk"
        self.adb.uploadfile(path, remotename)
        self.adb.shell("pm install -r \"%s\"" % remotename)
        # todo: check result.
        self.adb.shell("rm %s" % remotename)

    def instrument(self, className, args):
        """
        Run the specified package with instrumentation and return the output it 
        generates. Use this to run a test package using InstrumentationTestRunner.

          Args:
            className - The class to run with instrumentation. The format is 
                        packagename/classname. Use packagename to specify the Android 
                        package to run, and classname to specify the class to run 
                        within that package. For test packages, this is usually 
                        testpackagename/InstrumentationTestRunner
            args - A map of strings to objects containing the arguments to pass to 
                   this instrumentation (default value is None).
        """
        cmdline = ["am", "instrument", "-w", "-r"]
        for k, v in args:
            cmdline += [ k, str(v) ]
        cmdline += [ className ]

        # todo: parse 'instrument' result.
        return self.adb.shell(" ".join(quotespaces(_) for _ in cmdline))

    def press(self, name, type=DOWN_AND_UP):
        """
        Send a key event to the specified key

          Args:
            name - the keycode of the key to press (see android.view.KeyEvent)
            type - touch event type as returned by TouchPressType(). To simulate 
                   typing a key, send DOWN_AND_UP
        """
        if type==self.DOWN_AND_UP:
            self.mlib.keyevent(self.resolvekeyname(name))
        else:
            self.mlib.key(type, self.resolvekeyname(name))

    def reboot(self, into=None):
        """
        Reboots the specified device into a specified bootloader.

          Args:
            into - the bootloader to reboot into: bootloader, recovery, or None
        """
        self.adb.reboot(into)

    def removePackage(self, package):
        """
        Deletes the specified package from the device, including its associated data 
        and cache.

          Args:
            package - The name of the package to delete.
        """
        self.adb.shell("pm uninstall " + package)
        # todo: return result.

    def shell(self, cmd, timeout=0):
        """
        Executes an adb shell command and returns the result, if any.

          Args:
            cmd - The adb shell command to execute.
            timeout - This arg is optional. It specifies the maximum amount of time 
                      during which thecommand can go without any output. A value of 0 
                      means the methodwill wait forever. The unit of the timeout is 
                      millisecond
        """
        # todo: handle timeout
        return self.adb.shell(cmd)

    def takeSnapshot(self):
        """
        Gets the device's screen buffer, yielding a screen capture of the entire 
        display.
        """
        cap = self.adb.makecapture()
        return MonkeyImage(cap.capture())

    def touch(self, x, y, type):
        """
        Sends a touch event at the specified location

          Args:
            x - x coordinate in pixels
            y - y coordinate in pixels
            type - touch event type as returned by TouchPressType()
        """
        if type == self.DOWN_AND_UP:
            self.mlib.tap((x, y))
        else:
            self.mlib.touch(type, (x, y))

    def type(self, message):
        """
        Types the specified string on the keyboard. This is equivalent to calling press
        (keycode,DOWN_AND_UP) for each character in the string.

          Args:
            message - The string to send to the keyboard.
        """
        self.mlib.sendtext(message)

    def wake(self):
        """
        Wake up the screen on the device
        """
        self.mlib.wake()

# -- end of MonkeyDevice --

class MonkeyImage:
    """
    An image
    """

    def __init__(self, img):
        """
        Takes a Pillow.Image object
        """
        self.img = img


    def convertToBytes(self, format="png"):
        """
        Converts the MonkeyImage into a particular format and returns the result as a 
        String. Use this to get access to the rawpixels in a particular format. String 
        output is for better performance.

          Args:
            format - The destination format (for example, 'png' for Portable Network 
                     Graphics format). The default is png.
        """
        return self.img.tobytes(encoder_name=format)

    def getRawPixel(self, x, y):
        """
        Get a single ARGB (alpha, red, green, blue) pixel at location x,y. The 
        arguments x and y are 0-based, expressed in pixel dimensions. X increases to 
        the right, and Y increases towards the bottom. This method returns a tuple.

          Args:
            x - the x offset of the pixel
            y - the y offset of the pixel
        """
        r, g, b, a = self.img.getpixel((x,y))

        return a, r, g, b

    def getRawPixelInt(self, x, y):
        """
        Get a single ARGB (alpha, red, green, blue) pixel at location x,y. The 
        arguments x and y are 0-based, expressed in pixel dimensions. X increases to 
        the right, and Y increases towards the bottom. This method returns an Integer.

          Args:
            x - the x offset of the pixel
            y - the y offset of the pixel
        """
        r, g, b = self.img.getpixel((x,y))

        return (255<<24) + (r<<16) + (g<<8) + b

    def getSubImage(self, rect):
        """
        Copy a rectangular region of the image.

          Args:
            rect - A tuple (x, y, w, h) describing the region to copy. x and y specify 
                   upper lefthand corner of the region. w is the width of the region 
                   in pixels, and h is its height.
        """
        (x, y, w, h) = rect
        return MonkeyImage(self.img.crop( (x, y, x+w, y+h) ))

    def sameAs(self, other, percent=1.0):
        """
        Compare this MonkeyImage object to aother MonkeyImage object.

          Args:
            other - The other MonkeyImage object.
            percent - A float in the range 0.0 to 1.0, indicating the percentage of 
                      pixels that need to be the same for the method to return 'true'. 
                      Defaults to 1.0.
        """
        # todo

    def writeToFile(self, path, format=None):
        """
        Write the MonkeyImage to a file.  If no format is specified, this method 
        guesses the output format based on the extension of the provided file 
        extension. If it is unable to guess the format, it uses PNG.

          Args:
            path - The output filename, optionally including its path
            format - The destination format (for example, 'png' for  Portable Network 
                     Graphics format.
        """

        self.img.save(path, format)

# -- end of MonkeyImage --


class MonkeyRect:
    """
    Represents the coordinates of a rectangular object


    Fields: 
      left - The x coordinate of the left side of the rectangle
      top - The y coordinate of the top side of the rectangle
      right - The x coordinate of the right side of the rectangle
      bottom - The y coordinate of the bottom side of the rectangle
    """
    def __init__(self, l, t, r, b):
        self.left = l
        self.top = t
        self.right = r
        self.bottom = b

    def getCenter(self):
        """
        Returns a two item list that contains the x and y value of the center of the 
        rectangle
        """
        return [ left + self.getWidth() / 2, top + self.getHeight() / 2 ]

    def getHeight(self):
        """
        Returns the height of the rectangle
        """
        return self.bottom - self.top

    def getWidth(self):
        """
        Returns the width of the rectangle
        """
        return self.right - self.left

# -- end of MonkeyRect --

class MonkeyView:
    """
    Represents a view object.
    """

    def getAccessibilityIds(self):
        """
        Returns the accessibility ids of the current view
        """

    def getChecked(self):
        """
        Get the checked status of the view
        """

    def getChildren(self):
        """
        Returns the children of the current view
        """

    def getEnabled(self):
        """
        Returns the enabled status of the view
        """

    def getFocused(self):
        """
        Returns the focused status of the view
        """

    def getLocation(self):
        """
        Returns the location of the view in the form of a MonkeyRect
        """

    def getParent(self):
        """
        Returns the parent of the current view
        """

    def getSelected(self):
        """
        Returns the selected status of the view
        """

    def getText(self):
        """
        Returns the text contained by the view
        """

    def getViewClass(self):
        """
        Returns the class name of the view
        """

    def setFocused(self, focused):
        """
        Sets the focused status of the view

          Args:
            focused - The boolean value to set focused to
        """

    def setSelected(self, selected):
        """
        Sets the selected status of the view

          Args:
            selected - The boolean value to set selected to
        """

# -- end of MonkeyView --

class EasyMonkeyDevice:
    """
    MonkeyDevice with easier methods to refer to objects.
    """


    def __findattr_ex__(self):
        """
        Forwards unknown methods to the original MonkeyDevice object.
        """

    def exists(self, selector):
        """
        Checks if the specified object exists.

          Args:
            selector - The selector identifying the object.
        """

    def getFocusedWindowId(self):
        """
        Gets the id of the focused window.
        """

    def getText(self, selector):
        """
        Obtain the text in the selected input box.

          Args:
            selector - The selector identifying the object.
        """

    def locate(self, selector):
        """
        Locates the coordinates of the selected object.

          Args:
            selector - The selector identifying the object.
        """

    def touch(self, selector, type):
        """
        Sends a touch event to the selected object.

          Args:
            selector - The selector identifying the object.
            type - The event type as returned by TouchPressType().
        """

    def type(self, selector, text):
        """
        Types a string into the specified object.

          Args:
            selector - The selector identifying the object.
            text - The text to type into the object.
        """

    def visible(self, selector):
        """
        Checks if the specified object is visible.

          Args:
            selector - The selector identifying the object.
        """

# -- end of EasyMonkeyDevice -- 

class By:

    def id(self, id):
        """
        Select an object by id.

          Args:
            id - The identifier of the object.
        """

# -- end of By --

