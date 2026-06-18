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

def openFolder(editor):
	if hasattr(editor, "signals"):
		from PyQt6.QtWidgets import QFileDialog
		folder = QFileDialog.getExistingDirectory(
			None,
			"Open Folder",
			editor.explorerPath,
			QFileDialog.Option.ShowDirsOnly
		)
		if folder:
			editor.explorerPath = folder
			if hasattr(editor, "qtWindow"):
				editor.qtWindow.explorer.rebuild()
			editor.status = f"Folder: {folder}"
			editor.statusTimer = 120
			editor.notifyChanged()
	else:
		editor.status = "OPEN FOLDER: type path and press ENTER"
		editor.folderInputMode = True
		editor.folderInput = ""
		editor.notifyChanged()