class Layout:
	def __init__(self, editor):
		self.editor = editor
		self.lineNumberWidth = 6

	def paneWidth(self):
		h, w = self.editor.stdscr.getmaxyx()
		width = w - 2

		if self.editor.showExplorer:
			width -= self.editor.explorerWidth + 1
		return max(20, width // len(self.editor.panes))

	def paneStartX(self, paneIndex):
		startX = 1
		if self.editor.showExplorer:
			startX += self.editor.explorerWidth + 1
		
		startX += paneIndex * self.paneWidth()

		return startX

	def textStartX(self, paneIndex):
		return (
			self.paneStartX(paneIndex) + self.lineNumberWidth
		)

	def paneVisibleHeight(self):
		h, _ = self.editor.stdscr.getmaxyx()

		return h - 2
