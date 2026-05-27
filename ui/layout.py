class Layout:
	def __init__(self):
		self.panels = []

	def addPanel(self, panel):
		self.panels.append(panel)

	def visiblePanels(self):
		return [p for p in self.panels if p.visible]