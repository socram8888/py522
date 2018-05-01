
class ReaderException(Exception):
	def __init__(self, message=''):
		super().__init__(message)

class NoReplyException(Exception):
	def __init__(self):
		super().__init__('Tag did not reply')

class InvalidBCCException(Exception):
	def __init__(self, expected, calculated):
		super().__init__('Expecting BCC %02X, got %02X' % (expected, calculated))

		self.expected = expected
		self.calculated = calculated
