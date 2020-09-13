
import time
from enum import Enum
from py522.exceptions import NoReplyException, InvalidBCCException, ReaderException

class RC522:
	class Reg:
		Command = 0x01
		ComlEn = 0x02
		DivlEn = 0x03
		ComIrq = 0x04
		DivIrq = 0x05
		Error = 0x06
		Status1 = 0x07
		Status2 = 0x08
		FIFOData = 0x09
		FIFOLevel = 0x0A
		WaterLevel = 0x0B
		Control = 0x0C
		BitFraming = 0x0D
		Coll = 0x0E
		Mode = 0x11
		TxMode = 0x12
		RxMode = 0x13
		TxControl = 0x14
		TxASK = 0x15
		TxSel = 0x16
		RxSel = 0x17
		RxThreshold = 0x18
		Demod = 0x19
		MfTx = 0x1C
		MfRx = 0x1D
		SerialSpeed = 0x1F
		CRCResult = 0x21
		ModWidth = 0x24
		RFCfg = 0x26
		GsN = 0x27
		CWGsP = 0x28
		ModGsP = 0x29
		TMode = 0x2A
		TPrescaler = 0x2B
		TestSel1 = 0x31
		TestSel2 = 0x32
		TestPinEn = 0x33
		TestPinValue = 0x34
		TestBus = 0x35
		AutoTest = 0x36
		Version = 0x37
		AnalogTest = 0x38
		TestDAC1 = 0x39
		TestDAC2 = 0x3A
		TestADC = 0x3B

		def name(offset):
			for k, v in RC522.Reg.__dict__.items():
				if offset == v:
					return k

	CmdIdle = 0x0
	CmdMem = 0x1
	CmdGenRndId = 0x2
	CmdCalcCrc = 0x3
	CmdTransmit = 0x4
	CmdNoChange = 0x7
	CmdReceive = 0x8
	CmdTransceive = 0xC
	CmdMfAuth = 0xE
	CmdSoftReset = 0xF

	class Version(Enum):
		UNKNOWN = 0
		MFRC522_V1 = 1
		MFRC522_V2 = 2
		FM17522 = 3

	def __init__(self):
		self.collision = None
		self._tx_crc_enabled = None
		self._rx_crc_enabled = None

	def antenna_on(self):
		self._regwrite(RC522.Reg.TxControl, 0x83)

	def antenna_off(self):
		self._regwrite(RC522.Reg.TxControl, 0x80)

	def reset(self):
		self.soft_reset()

	def soft_reset(self):
		self._run_command(RC522.CmdSoftReset)
		time.sleep(0.05)
		if self._regread(RC522.Reg.Command) & 0x10:
			raise ReaderException('PCD has not left powerdown mode after reset')

		self._regwrite(RC522.Reg.TxASK, 0x40)
		self._regwrite(RC522.Reg.Mode, 0x3D)

		# Zero bits after collision
		self._regwrite(RC522.Reg.Coll, 0x80)

		self.antenna_on()

	def scan(self, wakeup=False):
		self._enable_crc(False)

		if wakeup:
			self._transceive_bits(b'\x52', 7)
		else:
			self._transceive_bits(b'\x26', 7)

		knownuid = bytearray()

		for ct in range(1, 4):
			anticol = bytearray([0x91 + ct * 2, 0, 0, 0, 0, 0, 0])
			goodcount = 0

			self._enable_crc(False)

			while goodcount < 40:
				anticol[1] = (2 + goodcount // 8) << 4 | (goodcount % 8)
				(recv, recvcol) = self._transceive_bits(anticol, 16 + goodcount, goodcount % 8)

				oldgood = goodcount
				if recvcol is not None:
					lastbyte = recvcol // 8
					recv = recv[0 : lastbyte + 1]
					recv[lastbyte] = recv[lastbyte] & 0xFF >> (7 - recvcol % 8)
					goodcount = goodcount + recvcol + 1
				else:
					goodcount = 40

				for pos in range(oldgood // 8, (goodcount + 7) // 8):
					anticol[2 + pos] = anticol[2 + pos] | recv[pos - oldgood // 8]


			calculatedBcc = anticol[2] ^ anticol[3] ^ anticol[4] ^ anticol[5]
			expectedBcc = anticol[6]
			if calculatedBcc != expectedBcc:
				raise InvalidBCCException(expected=expectedBcc, calculated=calculatedBcc)

			anticol[1] = 0x70
			resp = self.transceive(anticol)
			if anticol[2] != 0x88 or ct == 3:
				knownuid.extend(anticol[2:6])
				return knownuid

			knownuid.extend(anticol[3:6])

	def select(self, uid):
		assert(len(uid) in [4, 7, 10])

		self._enable_crc(False)
		self._transceive_bits(b'\x26', 7)

		ct = 1
		while len(uid) > 0:
			cmd = bytearray([0x91 + ct * 2, 0x70])
			if len(uid) > 4:
				cmd.append(0x88)
				cmd.extend(uid[0:3])
				uid = uid[3:]
			else:
				cmd.extend(uid)
				uid = b''

			# Generate BCC
			cmd.append(cmd[2] ^ cmd[3] ^ cmd[4] ^ cmd[5])

			resp = self.transceive(cmd)
			ct = ct + 1

	def send(self, request):
		self._prepare_tx(request)

		self._enable_crc(True)

		# Now run command
		self._run_command(RC522.CmdTransmit)

		self._wait_tx()

	def transceive(self, request):
		self._prepare_tx(request)

		self._enable_crc(True)

		self._run_command(RC522.CmdTransceive)
		self._regwrite(RC522.Reg.BitFraming, 0x80)

		self._wait_rx()

		return self._read_fifo()

	def halt(self):
		self.send(b'\x50\x00')

	def get_version(self):
		verid = self._regread(RC522.Reg.Version)
		if verid == 0x91:
			return RC522.Version.MFRC522_V1
		if verid == 0x92:
			return RC522.Version.MFRC522_V2
		if verid == 0x88:
			return RC522.Version.FM17522
		print('Unknown version: %02X' % verid)
		return RC522.Version.UNKNOWN

	def _run_command(self, cmd):
		rcvoff = 1
		if cmd == RC522.CmdReceive or cmd == RC522.CmdTransceive or cmd == RC522.CmdMfAuth:
			rcvoff = 0

		self._regwrite(RC522.Reg.Command, cmd | rcvoff << 5)

	def _read_fifo(self):
		count = self._regread(RC522.Reg.FIFOLevel) & 0x7F
		return self._regreadbulk(RC522.Reg.FIFOData, count)

	def _prepare_tx(self, request):
		# Stop any running command
		self._run_command(RC522.CmdIdle)

		# Clear IRQs
		self._regwrite(RC522.Reg.ComIrq, 0x7F)

		# Write data to FIFO
		self._regwritebulk(RC522.Reg.FIFOData, request)

	def _wait_rx(self):
		for x in range(1, 5):
			if self._regread(RC522.Reg.ComIrq) & 0x20:
				return

		# Clear FIFO reg
		self._regwrite(RC522.Reg.FIFOLevel, 0x80)

		raise NoReplyException()

	def _wait_tx(self):
		for x in range(1, 5):
			if self._regread(RC522.Reg.ComIrq) & 0x40:
				return

		# Clear FIFO reg
		self._regwrite(RC522.Reg.FIFOLevel, 0x80)

		raise ReaderException('Timed out while waiting for datagram transmission')

	def _transceive_bits(self, request, bitlen=None, rxalign=0):
		if bitlen is not None:
			fullbytes = (bitlen + 7) // 8
			request = request[0 : fullbytes]
			trailing_bits = bitlen & 0x7
		else:
			trailing_bits = 0

		self._prepare_tx(request)

		# Now run command
		self._run_command(RC522.CmdTransceive)

		# Configure framing and begin send
		self._regwrite(RC522.Reg.BitFraming, 0x80 | rxalign << 4 | trailing_bits)

		self._wait_rx()

		col = self._regread(RC522.Reg.Coll)
		if col & 0x20:
			col = None
		else:
			col = (col & 0x1F) - 1

		return (self._read_fifo(), col)

	def _enable_crc(self, enable):
		self._enable_tx_crc(enable)
		self._enable_rx_crc(enable)

	def _enable_tx_crc(self, enable):
		enable = bool(enable)
		if enable != self._tx_crc_enabled:
			if enable:
				self._regwrite(RC522.Reg.TxMode, 0x80)
			else:
				self._regwrite(RC522.Reg.TxMode, 0x00)
			self._tx_crc_enabled = enable

	def _enable_rx_crc(self, enable):
		enable = bool(enable)
		if enable != self._rx_crc_enabled:
			if enable:
				self._regwrite(RC522.Reg.RxMode, 0x80)
			else:
				self._regwrite(RC522.Reg.RxMode, 0x00)
			self._rx_crc_enabled = enable
