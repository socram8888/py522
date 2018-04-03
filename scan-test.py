#!/usr/bin/env python3

import time
import sys
from py522.rc522uart import RC522Uart

if len(sys.argv) != 2:
	print('Usage: %s <serial port>' % sys.argv[0], file=sys.stderr)
	sys.exit(1)

rc = RC522Uart(sys.argv[1])

rc.port.dtr = True
time.sleep(0.1)
rc.port.dtr = False
time.sleep(0.1)

rc.reset()

while True:
	uid = rc.scan()
	while uid != None:
		rc.halt()
		print(uid)
		uid = rc.scan()

	time.sleep(0.1)
