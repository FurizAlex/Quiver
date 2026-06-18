class Layout:
	def __init__(self, editor):
		self.editor = editor
		self.lineNumberWidth = 6

	def paneWidth(self):
		width = self.editor.screenWidth - 2

		if self.editor.showExplorer:
			width -= self.editor.explorerWidth + 1
		n = len(self.editor.panes)
		width -= (n - 1)
		return max(20, width // n)

	def paneStartX(self, paneIndex):
		startX = 1
		if self.editor.showExplorer:
			startX += self.editor.explorerWidth + 1
		startX += paneIndex * (self.paneWidth() + 1)
		return startX

	def textStartX(self, paneIndex):
		return (
			self.paneStartX(paneIndex) + self.lineNumberWidth
		)

	def paneVisibleHeight(self):
		return self.editor.screenHeight - 2