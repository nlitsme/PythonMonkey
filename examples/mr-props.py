"""
Lists all MonkeyDevice properties.
"""
from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice, MonkeyImage, MonkeyRect, MonkeyView

import sys

if sys.version_info[0] == 2:
    function = """
def xprint(*args, **kwargs):
    for val in args:
        print val,
    if kwargs.get('end'):
        print kwargs.get('end'),
    else:
        print
    """
    exec(function)
else:
    unicode = str
    function = """
def xprint(*args, **kwargs):
    print(*args, **kwargs)
    """
    exec(function)


mr = MonkeyRunner()

dev = MonkeyRunner.waitForConnection(99)
for name in dev.getPropertyList():
    xprint("%-20s\t%s" % (name, dev.getProperty(name)))


