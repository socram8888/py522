#!/usr/bin/env python3

from py522.reader import RC522Uart
from py522.tag import UltralightC
import sys

if len(sys.argv) != 2:
	print('Usage: %s <serial port>' % sys.argv[0], file=sys.stderr)
	sys.exit(1)

rc = RC522Uart(sys.argv[1])
rc.reset()

print("Reader version: %s" % rc.get_version())

detected = rc.scan()
print('Detected tag: %s' % detected.hex())

print('Version: %s' % rc.transceive(b'\x60').hex())

ul = UltralightC(rc)
ul.authenticate(bytes.fromhex('49454D4B41455242214E4143554F5946'))

print('Authentication suceeded!')
