
from .rc522 import RC522
import serial

class RC522Uart(RC522):
	def __init__(self, port, speed=9600):
		super().__init__()
		self.port = serial.Serial(port, speed, timeout=1)

	def _regread(self, reg):
		return self._regreadbulk(reg)[0]

	def _regreadbulk(self, reg, count=1):
		assert(reg >= 0 and reg <= 0x3F)
		req = bytes([reg | 0x80])

		data = bytearray()
		while len(data) < count:
			if self.port.write(req) != 1:
				raise Exception('Could not send read request')

			try:
				data.extend(self.port.read())
			except Exception as e:
				raise Exception('Could not read register value')

		#print('%s -> %s' % (RC522.Reg.name(reg), data.hex()))
		return data

	def _regwrite(self, reg, value):
		value = bytes([value])
		return self._regwritebulk(reg, value)

	def _regwritebulk(self, reg, data):
		assert(reg >= 0 and reg <= 0x3F)
		#print('%s <- %s' % (RC522.Reg.name(reg), data.hex()))
		req = bytes([reg])

		for pos in range(0, len(data)):
			if self.port.write(req) != 1:
				raise Exception('Could not send write request')

			ack = self.port.read()
			if ack != req:
				raise Exception('Incorrect write acknowledgement from PCD: expected %s, got %s' % (req, ack))

			if self.port.write(data[pos : pos + 1]) != 1:
				raise Exception('Could not write register value')
