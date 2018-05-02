#!/usr/bin/env python3

import time
import sys
from py522.reader import RC522Uart

if len(sys.argv) != 2:
	print('Usage: %s <serial port>' % sys.argv[0], file=sys.stderr)
	sys.exit(1)

rc = RC522Uart(sys.argv[1])
rc.hard_reset()
rc.reset()

print("Reader version: %s" % rc.get_version())

while True:
	try:
		uid = rc.scan()
	except:
		continue

	print("Found tag: %s" % uid.hex())
	rc.halt()
	time.sleep(0.1)

