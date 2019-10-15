import os
import time
from collections import defaultdict

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice, MonkeyImage

"""

execute with:

$ANDROID_HOME/tools/bin/monkeyrunner originalmonkey.py

"""

def hasGreenPlus(img):
    try:
        plusarea = img.getSubImage( (1855, 90, 40, 35) )

        ref = defaultdict(int)
        for y in range(35):
            for x in range(40):
                a, r, g, b = plusarea.getRawPixel(x, y)
                rgb = "%x%x%x" % (r>>5, g>>5, b>>5)
                ref[rgb] += 1

        return ref["350"] > 400 and ref["777"] > 200
    except:
        print("error in find plus")
        return

def waitForGreenPlus(dev):
    i = 0
    t = time.time()
    while time.time() - t < 30:
        print("Plus wait loop")
        img = dev.takeSnapshot()
        img.writeToFile("test_%03d.png" % i, "png")
        if hasGreenPlus(img):
            return True
        time.sleep(0.1)

        i += 1

def findSculptor(img):
    count = defaultdict(lambda:defaultdict(int))
    for y in range(200, 800):
        for x in range(200, 1700):
            a, r, g, b = img.getRawPixel(x, y)
            rgb = "%x%x%x" % (r>>5, g>>5, b>>5)
            if rgb in ("022", "023", "032", "033"):
                count[x//10][y//10] += 1
    found = None
    for x in sorted(count.keys()):
        for y in sorted(count[x].keys()):
            if count[x][y] + count[x+1][y] + count[x][y+1] + count[x+1][y+1] > 320:
                print("found (%d,%d) - %d %d %d %d" % ( x, y,
                        count[x][y], count[x+1][y], count[x][y+1], count[x+1][y+1]))
                found = (x*10, y*10)
    
    return found

def scrollToSculptor(dev):
    l, r = 600, 800
    t, b = 600, 800
    for i in range(10):
        print("sculptor wait loop")
        img = dev.takeSnapshot()
        img.writeToFile("zoom_%03d.png" % i, "png")

        p = findSculptor(img)
        if p:
            return p

        dev.drag((600, 600), (600, 800), 1.0, 10)   # -> S
        time.sleep(0.1)

def wiggle(dev):
    l, r = 600, 800
    t, b = 600, 800
    for _ in range(40):
        dev.drag((l, t), (r, b), 1.0, 10)   # -> SE
        time.sleep(0.1)
        dev.drag((r, t), (l, b), 1.0, 10)   # -> SW
        time.sleep(0.1)
        dev.drag((r, b), (l, t), 1.0, 10)   # -> NW
        time.sleep(0.1)
        dev.drag((l, b), (r, t), 1.0, 10)   # -> NE
        time.sleep(0.1)

def main():
    print("LAUNCHING")
    dev = MonkeyRunner.waitForConnection(99, '159ef44f')
    dev.startActivity(component="com.supercell.boombeach/.GameApp")

    # sequence of screens:
    #  * black screen
    #  * "super cell"  logo
    #  * "boombeach" loading
    #  * zoomed out island  -- waitForGreenPlus
    #  * zoomed in island

    print("WAITING")
    if not waitForGreenPlus(dev):
        return

    time.sleep(1)   # wait for zoom

    print("SCROLLING")
    p = scrollToSculptor(dev)
    if not p:
        return

    # click the sculptor
    dev.touch( p[0], p[1], MonkeyDevice.DOWN_AND_UP)

    while True:
        # open the sculptor menu
        time.sleep(0.5)
        dev.touch( p[0] + 54, p[1] + 164, MonkeyDevice.DOWN_AND_UP)

        # select the life tab
        time.sleep(0.5)
        dev.touch( 315, 168, MonkeyDevice.DOWN_AND_UP)
        # click the 'idol'
        time.sleep(0.5)
        dev.touch( 480, 600, MonkeyDevice.DOWN_AND_UP)

        # wait
        time.sleep(11.0)

        # open the sculptor menu
        time.sleep(0.5)
        dev.touch( p[0] + 54, p[1] + 164, MonkeyDevice.DOWN_AND_UP)

        # click 'salvage statue'
        time.sleep(0.5)
        dev.touch( 1454, 696, MonkeyDevice.DOWN_AND_UP)

        # click confirm salvage
        time.sleep(0.5)
        dev.touch( 1170, 850, MonkeyDevice.DOWN_AND_UP)


    print("SUCCESS", p)

main()

