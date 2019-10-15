from __future__ import print_function, division
from convertbbcrystals import BoomBeach
from PIL import Image
import sys

def dumpbutton(img):
    """
    # 1295-1600, 620-765 -- full button
    """
    if img.width < img.height:
        return
    for y in range(620, 765):
        for x in range(1295, 1600):
            r, g, b, a = img.getpixel((x,y))
            c = "%x%x%x" % (((r>>5)-1)>>1, g>>6, b>>6)
            print(c, end=" ")
        print()

bb = BoomBeach(None)

for fn in sys.argv[1:]:
    try:
        print("==>", fn, "<==")
        img = Image.open(fn)
        print("size=%s, w=%s, h=%s" % (img.size, img.width, img.height))
        print("pixel: %s" % (img.getpixel( (img.width//2, img.height//2)), ))
        print("plus: %s" % bb.hasGreenPlus(img))
        print("sculpt: %s" % (bb.findSculptor(img),))
        print("status: %s" % (bb.findSculptorStatus(img),))
        #dumpbutton(img)
    except Exception as e:
        print("ERR", e)
