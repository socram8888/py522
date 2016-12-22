
import pyDes
import os

class UltralightC:
	def __init__(self, pnd):
		self.pnd = pnd
		self.authenticated = False

	def authenticate(self, key):
		beginReply = self.pnd.transceive(b'\x1A\x00')

		if len(beginReply) != 9 or beginReply[0] != 0xAF:
			raise Exception('Invalid auth start response from card: "%s"' % beginReply.hex())

		rndA = os.urandom(8)
		rndAPrime = rndA[1:] + rndA[0:1]

		encryptedRndB = beginReply[1:]
		rndB = pyDes.triple_des(key, pyDes.CBC, bytes(8)).decrypt(encryptedRndB)

		pndAuth = rndA + rndB[1:] + rndB[0:1]
		pndAuth = pyDes.triple_des(key, pyDes.CBC, encryptedRndB).encrypt(pndAuth)

		authReply = self.pnd.transceive(b'\xAF' + pndAuth)

		if len(authReply) != 9 or authReply[0] != 0x00:
			raise Exception('Invalid auth reply from card: "%s"' % authReply.hex())

		cardRotatedA = pyDes.triple_des(key, pyDes.CBC, pndAuth[8:]).decrypt(authReply[1:])
		if cardRotatedA != rndA[1:] + rndA[0:1]:
			raise Exception('Card authentication failure')
