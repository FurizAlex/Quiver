class DiagnosticManager:
	def __init__(self):
		self.items = []

	def clear(self):
		self.items.clear()

	def add(self, diagnostic):
		self.items.append(diagnostic)

	def all(self):
		return self.items

	def count(self):
		return len(self.items)

	def atLine(self, line):
		return [d for d in self.items if d.line == line]