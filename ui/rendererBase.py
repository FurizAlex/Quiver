class RendererBase:
	def initialize(self):
		pass

	def draw(self, editor):
		raise NotImplementedError

	def drawText(self, x, y, text, style=0):
		raise NotImplementedError

	def drawLine(self, x1, y1, x2, y2, style=0):
		raise NotImplementedError

	def clear(self):
		raise NotImplementedError

	def present(self):
		raise NotImplementedError

	def shutdown(self):
		pass