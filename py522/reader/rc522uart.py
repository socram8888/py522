
from .rc522 import RC522
from py522.exceptions import NoReplyException, InvalidBCCException, ReaderException
import serial
import time

class RC522Uart(RC522):
	BAUD_REG_VALUE = {
		7200: 0xFA,
		9600: 0xEB,
		14400: 0xDA,
		19200: 0xCB,
		38400: 0xAB,
		57600: 0x9A,
		115200: 0x7A,
		128000: 0x74,
		230400: 0x5A,
		460800: 0x3A,
		921600: 0x1C,
		1228800: 0x15
	}

	def __init__(self, port, speed=9600):
		super().__init__()
		self.port = serial.Serial(port, speed, timeout=1)
		self.hard_reset_negated = False

	def reset(self):
		self.hard_reset()
		self.soft_reset()

		# On reset, baud rate gets reset as well
		self.port.baudrate = 9600

	def hard_reset(self):
		self.port.dtr = not self.hard_reset_negated
		time.sleep(0.01)
		self.port.dtr = self.hard_reset_negated
		time.sleep(0.01)

	def change_baud_rate(self, new_speed):
		reg_value = RC522Uart.BAUD_REG_VALUE.get(new_speed)
		if reg_value == None:
			raise ReaderException('Unsupported baudrate %s' % str(new_speed))
		self._regwrite(RC522.Reg.SerialSpeed, reg_value)
		self.port.baudrate = new_speed

	def _regread(self, reg):
		return self._regreadbulk(reg)[0]

	def _regreadbulk(self, reg, count=1):
		assert(reg >= 0 and reg <= 0x3F)
		req = bytes([reg | 0x80]) * count

		if self.port.write(req) != len(req):
			raise ReaderException('Could not send read request')

		data = self.port.read(count)
		if len(data) != count:
			raise ReaderException('Could not read register value')

		#print('%s -> %s' % (RC522.Reg.name(reg), data.hex()))
		return data

	def _regwrite(self, reg, value):
		value = bytes([value])
		return self._regwritebulk(reg, value)

	def _regwritebulk(self, reg, data):
		assert(reg >= 0 and reg <= 0x3F)
		#print('%s <- %s' % (RC522.Reg.name(reg), data.hex()))

		req = bytearray()
		for b in data:
			req.append(reg)
			req.append(b)

		if self.port.write(req) != len(req):
			raise ReaderException('Could not send write request')

		ack = self.port.read(len(data))
		if ack != bytes([reg]) * len(data):
			raise ReaderException('Incorrect write acknowledgement from PCD')
