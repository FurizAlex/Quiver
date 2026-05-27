class Clipboard:
	def __init__(self):
		self.data = ""

	def copy(self, text):
		self.data = text

	def paste(self):
		return self.data