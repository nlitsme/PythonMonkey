from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice, MonkeyImage, MonkeyRect, MonkeyView
from com.android.monkeyrunner.easy import EasyMonkeyDevice, By

mr = MonkeyRunner()
print "al->", mr.alert("alert message")
print "ch->", mr.choice("choice message", ["first", "second", "third"])
print "in->", mr.input("input something", "dfl", "input", "oktit", "cantit")
# print mr.help()
dev = MonkeyRunner.waitForConnection(99, '159ef44f')

hv = dev.getHierarchyViewer()

