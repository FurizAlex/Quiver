from ui.pane import Pane

def toggleExplorer(editor):
	editor.showExplorer = (not editor.showExplorer)

def splitPane(editor):
	current = editor.pane

	newPane = Pane(current.buffer)
	newPane.cursorX = current.cursorX
	newPane.cursorY = current.cursorY

	editor.panes.append(newPane)

	editor.activePane = (len(editor.panes) - 1)
	editor.notifyPanesChanged()

def closePane(editor):
	if len(editor.panes) <= 1:
		editor.status = "Cannot Close Only Pane"
		return
	editor.panes.pop(editor.activePane)
	editor.activePane = min(editor.activePane, len(editor.panes) - 1)
	editor.status = "Pane Closed"
	editor.notifyPanesChanged()

def nextPane(editor):
	editor.activePane = ((editor.activePane + 1) % len(editor.panes))