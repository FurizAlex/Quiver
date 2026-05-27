class Panel:
	def __init__(self, x, y, width, height):
		self.x = x
		self.y = y

		self.width = width
		self.height = height

		self.visible = True

class FileExplorerPanel(Panel):
	def __init__(self):
		super().__init__(0, 0, 30, 20)

		self.files = []

class TerminalPanel(Panel):
	def __init__(self):
		super().__init__(0, 20, 100, 10)