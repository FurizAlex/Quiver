from ui.pane import Pane

def toggleExplorer(editor):
	editor.showExplorer = (not editor.showExplorer)

def splitPane(editor):
	current = editor.pane

	newPane = Pane(current.bufferIndex)
	newPane.cursorX = current.cursorX
	newPane.cursorY = current.cursorY

	editor.panes.append(newPane)

	editor.activePane = (len(editor.panes) - 1)

def nextPane(editor):
	editor.activePane = ((editor.activePane + 1) % len(editor.panes))