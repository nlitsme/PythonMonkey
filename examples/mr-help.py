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

def dump(obj):
    xprint("{")
    xprint(obj.__name__)
    xprint(obj.__doc__)
    xprint()
    for k in dir(obj):
        if k.startswith('__'):
            continue
        try:
            v = getattr(obj, k)
            xprint(k, "\t", type(v), "\t", v)
            if type(v) != unicode:
                xprint(v.__doc__)
                xprint()
        except:
            _, e, _ = sys.exc_info()
            xprint(k, "\t", "ERROR -->", e)
    xprint("}")

dump(MonkeyRunner)
dump(MonkeyDevice)
dump(MonkeyImage)
dump(MonkeyRect)
dump(MonkeyView)
