# PythonMonkey

A python library for writing automatic UI testing tools.

This module is a replacement for the Jython monkeyrunner library that comes with the Android SDK.


## monkeyrunner compatibility layer

The monkeyrunner module is (almost) a drop-in replacement for the com.android.monkeyrunner
Jython module. There is an issue with python 2 vs 3 language compatibility. The Jython
interpreter shipped with the android SDK is quite old, it supports python 2.5.3.
This python version does not have any of tbe future compatibility features which came with
v2.6 and v2.7. This makes writing code which works both on python 3.x and in the Jython
environnent a bit more difficult. Mostly this means, you can not use the print function,
and you will have to use `sys.exc_info()` to access the most recent exception.

To be able to use this module, create a subdirectory `com/android`, and put a symbolic link
to the monkeyrunner.py file there.

Then run your monkey script using:

    python3 mymonkey.py


## Android sdk tools

### monkeyrunner

`monkeyrunner` is an Android SDK tool which runs Jython scripts in a context which provides access to various device resources.
 * [monkeyrunner](https://developer.android.com/studio/test/monkeyrunner) documentation
   * [MonkeyDevice](https://developer.android.com/studio/test/monkeyrunner/MonkeyDevice) for installing, launching and interacting with apps.
   * [MonkeyImage](https://developer.android.com/studio/test/monkeyrunner/MonkeyImage) for screenshots.
   * [MonkeyRunner](https://developer.android.com/studio/test/monkeyrunner/MonkeyRunner)

Google sourcecode:
 * [monkeyrunner](https://android.googlesource.com/platform/tools/swt/+/master/monkeyrunner/src/main/java/com/android/monkeyrunner)
 * [chimpchat](https://android.googlesource.com/platform/tools/swt/+/master/chimpchat/src/main/java/com/android/chimpchat)

`monkeyrunner` uses two tools on the device to accomplish it's tasks: `adb` and `monkey`.

To execute a Jython monkeyrunner script, type:

    $ANDROID_HOME/tools/bin/monkeyrunner mymonkey.py


### monkey

`monkey` is the tool running on the device providing the UI interaction support for `monkeyrunner`.
 * [monkey](https://developer.android.com/studio/test/monkey) documentation

As a standalone tool it can also be used to monkey-test a ui, by sending random taps to it.

Google sourcecode:
 * [monkey](https://android.googlesource.com/platform/development/+/master/cmds/monkey/src/com/android/commands/monkey)


### adb

`adb` is the tool for all developer interactions with android devices, 

 * [SERVICES.TXT](https://android.googlesource.com/platform/system/core/+/master/adb/SERVICES.TXT) has a list of all supported commands.
 * [adb](https://android.googlesource.com/platform/system/core/+/master/adb/) sourcecode


# Author

Willem Hengeveld <itsme@xs4all.nl>


