from __future__ import print_function, division
"""
This script automates some tedious tasks in the game BoomBeach.
it converts small crystals to larger crystals by sculpting statue's.

Crystals come in three sizes, and four flavours, the sizes: 'shard', 'fragment', and 'crystal',
and the flavours: 'life', 'ice', 'magma', 'dark'. Statues come in the same flavours, and also
three sizes: 'idol', 'guardian', and 'masterpiece'.

After sculpting a statue, you can choose to either place, store or salvage the statue.
Salvaging converts the statue into the next larger crystal type.

They convert like this:

    [7 shards] -> idol -> 1 fragment
    [7 fragments] -> guardian -> 1 crystal
    [7 crystals] -> masterpiece -> 7 powerstones

The powerstones are useful to boost your placed statues.

This works easiest for converting shards to fragments, where the sculpting
process takes only 10 seconds. However, that can also easily be done by
just clicking the 'convert' button in the shard's explanation popup.


TODO: get rid of double indirections: self.dev.adb.something()
TODO: improve sculptor button detection.

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
        print("screen=%s" % screenstate)

        if not screenstate:
            print("error getting devstate")
            return

        if screenstate == 'ON_UNLOCKED':
            print("already unlocked")
            return True

        if screenstate == 'OFF':
            print("turning on screen")
            self.mon.keyevent(26)   # screen on
        self.mon.keyevent(82)   # unlock
        time.sleep(0.5)
        if pin:
            print("entering pin")
            self.mon.sendtext(pin)
            time.sleep(0.1)
            self.mon.keyevent(66)   # enter pin

        time.sleep(0.5)
        screenstate = self.adb.devicestate()
        print("pin -> screen=%s" % screenstate)

        return screenstate == 'ON_UNLOCKED'



# types of crystals
LIFE_CRYSTAL = 0
ICE_CRYSTAL = 1
MAGMA_CRYSTAL = 2
DARK_CRYSTAL = 3

# sizes of crystals
CRYSTAL_SHARD = 0
CRYSTAL_FRAGMENT = 1
CRYSTAL_CRYSTAL = 2

# statue levels
IDOL_STATUE = 0
GUARDIAN_STATUE = 1
MASTERPIECE_STATUE = 2



class BoomBeach:
    def __init__(self, dev):
        self.dev = dev

    def start(self):
        # launch boombeach
        remotecmd = self.dev.adb.makeshell("am start -n com.supercell.boombeach/.GameApp")

        time.sleep(0.5)
        print("launch app->", remotecmd.read())

        print("WAITING")
        if not self.waitForPlus():
            return

        time.sleep(1)   # wait for zoom

        print("SCROLLING")
        self.scultorpos = self.scrollToSculptor()
        if not self.scultorpos:
            return

        # TODO: make sure all button's are off by clicking somewhere on
        # the background.

        print("found sculptor at %s" % (self.scultorpos,))
        # click the sculptor to show it's control buttons.
        #  -> either 2 or 3, depending on it's state.
        self.dev.mon.tap( self.scultorpos ) 

        which_type = LIFE_CRYSTAL
        which_statue = GUARDIAN_STATUE
        fixed_wait = None
        max_wait = 12.0
        open_progress = True

        i = 0
        while True:
            #self.dev.adb.takeSnapshot().save("%03d-sculptorbuttons.png" % i)
            print("sculpt loop")

            time.sleep(0.5)

            # check sculptor status: idle, busy, done
            status = self.getSculptorStatus()

            if status == 'IDLE':
                # select the the crystal flavour tab
                time.sleep(0.5)
                self.dev.mon.tap( (315 + 336*which_type, 168) )
                # click the statue type
                time.sleep(0.5)
                self.dev.mon.tap( (480 + 454*which_statue, 600) )
            elif status == 'BUSY':
                if which_statue == IDOL_STATUE:
                    self.waitForDone(10.0)
                else:
                    break
            elif status == 'DONE':
                self.clickSalvageStatue()
            else:
                print("opening sculptor menu")
                # open the sculptor menu
                # TODO: determine if the buttons are visible
                self.dev.mon.tap( self.scultorpos ) 
                time.sleep(0.1)
                self.dev.mon.tap( (self.scultorpos[0] + 54, self.scultorpos[1] + 164) )
                 
#           if fixed_wait:
#               print("waiting")
#               # wait
#               time.sleep(fixed_wait)

#           if not open_progress:
#               # open the sculptor menu
#               time.sleep(0.5)
#               self.dev.mon.tap( (self.scultorpos[0] + 54, self.scultorpos[1] + 164) )


    def waitForDone(self, max_wait):
        # open the 'busy' sculptor menu
        time.sleep(0.5)
        self.dev.mon.tap( (self.scultorpos[0] - 39, self.scultorpos[1] + 193) )

        if not self.waitForSculptingDone(max_wait):
            return


    def clickSalvageStatue(self):
            # click 'salvage statue'
            time.sleep(0.5)
            self.dev.mon.tap( (1454, 696) )

            # click confirm salvage
            time.sleep(0.5)
            self.dev.mon.tap( (1170, 850) )


    @staticmethod
    def hasGreenPlus(img):
        """
        Check if the green plus, next to the diamond count, is present in the picture.
        """
        if img.width < img.height:
            print("in portrait: %s" % (img.size,))
            # ignore screenshots in portrait mode.
            return

        try:
            ref = defaultdict(int)
            for y in range(35):
                for x in range(40):
                    r, g, b, a = img.getpixel( (1855+x, 90+y) )
                    rgb = "%x%x%x" % (r>>5, g>>5, b>>5)
                    ref[rgb] += 1

            print("350: %d, 777: %d" % (ref["350"], ref["777"]))

            return ref["350"] > 400 and ref["777"] > 200
        except:
            print("error in find plus")
            return

    def waitForPlus(self):
        """
        Wait until the green '+' sign is present next to the 'diamonds'.
        """
        i = 0
        t = time.time()
        while time.time() - t < 30:
            print("Plus wait loop")
            img = self.dev.adb.takeSnapshot()
            img.save("test_%03d.png" % i)
            if self.hasGreenPlus(img):
                return True
            time.sleep(0.1)

            i += 1

    @staticmethod
    def findSculptor(img):
        """
        Look for the sculptor in the image by looking for a 200x200 chunk
        with mostly the green sculptor roof color.
        """
        #  in these the sculptor building is always found,
        #     but the button location may vary depending on
        #     distance and zoom level.
        # sculptor-statue-building.png
        # sculpt-buttons2.png
        # sculpt-buttons3.png
        # sculpt-buttons4.png
        # sculpt-zoomed.png

        # ... when the buttons are visible, the color pulsates
        #    between light and dark green.
        # sculptor-buttons.png
        # sculpt-buttons1.png
        # sculpt-buttons5-zoom.png

        count = defaultdict(lambda:defaultdict(int))
        if img.size != (1920, 1080):
            return
        #print("--")
        for y in range(200, img.height-200):
            for x in range(200, img.width-200):
                r, g, b, a = img.getpixel( (x, y) )
                rgb = "%x%x%x" % (r>>5, g>>5, b>>5)
                #print(rgb, end=" ")
                if rgb in ("022", "023", "032", "033"):
                    count[y//10][x//10] += 1
            #print()
        def get(x,y):
            v = 0
            if y in count:
                if x in count[y]:
                    v = count[y][x]
            return v

    #   print("--")
    #   for y in range(img.height//10):
    #       for x in range(img.width//10):
    #           print(" %3d" % get(x,y), end="")
    #       print()

    #   print("--")
    #   for y in range(img.height//10):
    #       for x in range(img.width//10):
    #           print(" %3d" % (get(x,y) + get(x+1,y) + get(x,y+1) + get(x+1,y+1)), end="")
    #       print()

        found = None
        for y in sorted(count.keys()):
            for x in sorted(count[y].keys()):
                if get(x,y) + get(x+1,y) + get(x,y+1) + get(x+1,y+1) > 320:
                    #print("found (%d,%d) - %d %d %d %d" % ( x, y,
                    #        get(x, y), get(x+1, y), get(x, y+1), get(x+1, y+1)))
                    found = (x*10, y*10)
        
        return found


    def scrollToSculptor(self):
        """
        Checks if we can find the sculptor, keep scrolling upward,
        until the sculptor is found.
        """
        l, r = 600, 800
        t, b = 600, 800
        for i in range(10):
            print("sculptor wait loop")
            img = self.dev.adb.takeSnapshot()
            img.save("zoom_%03d.png" % i)

            p = self.findSculptor(img)
            if p:
                return p

            self.dev.mon.drag((600, 600), (600, 800), 1.0, 10)   # -> S
            time.sleep(0.1)

    def getSculptorStatus(self):
        img = self.dev.adb.takeSnapshot()
        return self.findSculptorStatus(img)

    @staticmethod
    def findSculptorStatus(img):
        """
        # analyze screenshot to determine the current status.
        # sculptor-busy.png             - light brown background
        # sculptor-statue-choice.png                                                       
        # sculptor-done.png             - has dark brown button with white + black letters

        checks if any of the 'choose sculpting action' buttons
        are present, by looking for the presence of the background color, or button color.

        # 1400-1500, 650-700 -- center
        # 1295-1600, 620-765 -- full button

        # 1150-1350,  50-100 -- title bar blue
        """
        if img.width < img.height:
            print("in portrait: %s" % (img.size,))
            # ignore screenshots in portrait mode.
            return

        lbrown = brown = black = white = 0
        for y in range(620, 765):
            for x in range(1295, 1600):
                r, g, b, a = img.getpixel((x,y))
                br = "%x%x%x" % (((r>>5)-1)>>1, g>>6, b>>6)
                bw = "%x%x%x" % (r>>5, g>>5, b>>5)
                if br == '221':
                    brown += 1
                elif bw == '000':
                    black += 1
                elif bw == '777':
                    white += 1
                elif br == '333':
                    lbrown += 1
                #print("%s:%s" % (br, bw), end=" ")
            #print()

        print("lbr=%d, br=%d, bl=%d, wh=%d" % (lbrown, brown, black, white))
        if (brown > 25000) and (4000 < black < 5000) and (5000 < white < 6000):
            return "DONE"
        elif lbrown > 35000:
            return "BUSY"

        blue = 0
        for y in range(50, 100):
            for x in range(1150, 1350):
                r, g, b, a = img.getpixel((x,y))
                bw = "%x%x%x" % (r>>5, g>>5, b>>5)
                if bw == '134':
                    blue += 1

        if blue > 8000:
            return "IDLE"
            


    @staticmethod
    def makesculptname():
        t = datetime.datetime.now()
        return "sculptor_%s.png" % (t.strftime("%y%m%d-%H%M%S"))


    def waitForSculptingDone(self, maxduration):
        """
        wait for 'duration' until the sculptor is done.
        """
        tstart = time.time()
        tend = tstart + maxduration
        while time.time() < tend:
            if self.getSculptorStatus() == "DONE":
                img.save(self.makesculptname())
                return True

            time.sleep(0.5)


def main():
    dev = DeviceInteraction()
    if not dev.connect("2642"):
        print("failed to unlock")
        return

    bb = BoomBeach(dev)

    bb.start()


if __name__=='__main__':
    main()
