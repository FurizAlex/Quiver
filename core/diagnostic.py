class Diagnostic:
	def __init__(self, line, column, severity, message):
		self.line = line
		self.column = column
		self.severity = severity
		self.message = message