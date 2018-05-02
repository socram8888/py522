
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
		super().reset()

		# On reset, baud rate gets reset as well
		self.port.baudrate = 9600

	def hard_reset(self):
		self.port.dtr = not self.hard_reset_negated
		time.sleep(0.01)
		self.port.dtr = self.hard_reset_negated
		time.sleep(0.01)

	def change_serial_speed(self, new_speed):
		self._regwrite(RC522.Reg.SerialSpeed, RC522Uart.BAUD_REG_VALUE[new_speed])
		self.port.baudrate = new_speed

	def _regread(self, reg):
		return self._regreadbulk(reg)[0]

	def _regreadbulk(self, reg, count=1):
		assert(reg >= 0 and reg <= 0x3F)
		req = bytes([reg | 0x80])

		data = bytearray()
		while len(data) < count:
			if self.port.write(req) != 1:
				raise ReaderException('Could not send read request')

			try:
				data.extend(self.port.read())
			except Exception as e:
				raise ReaderException('Could not read register value') from e

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
				raise ReaderException('Could not send write request')

			ack = self.port.read()
			if ack != req:
				raise ReaderException('Incorrect write acknowledgement from PCD: expected %s, got %s' % (req, ack))

			if self.port.write(data[pos : pos + 1]) != 1:
				raise ReaderException('Could not write register value')
