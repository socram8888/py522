
import time
from py522.rc522uart import RC522Uart
from py522.ultralightc import UltralightC

rc = RC522Uart('COM4')
		
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

#print(rc.scan()[0].hex())
#rc.select(b'\x04\x5a\xf6\x62\xd5\x4b\x80')

#print('>>> Version: %s' % rc.transceive(b'\x60').hex())

#ul = UltralightC(rc)
#ul.authenticate(bytes.fromhex('49454D4B41455242214E4143554F5946'))

#print('Authentication suceeded!')
