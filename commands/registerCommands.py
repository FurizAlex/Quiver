from commands.fileCommands import save
from commands.fileCommands import openFileBuffer
from commands.diagnosticCommands import nextDiagnostic
from commands.bufferCommands import nextBuffer, previousBuffer, closeBuffer
from commands.uiCommands import splitPane, closePane, nextPane, toggleExplorer
from commands.editCommands import undo, redo

def newFileCommand(editor):
	from input.insertMode import newFile
	newFile(editor)

def registerCommands(registry):
	registry.register("save_file", save, "Save File", "File")
	registry.register("next_buffer", nextBuffer, "Next Buffer", "Buffer")
	registry.register("previous_buffer", previousBuffer, "Previous Buffer", "Buffer")
	registry.register("new_file", newFileCommand, "New File", "File")
	registry.register("close_file", closeBuffer, "Close File", "File")
	registry.register("split_pane", splitPane, "Split Pane", "View")
	registry.register("close_pane", closePane, "Close Pane", "View")
	registry.register("next_pane", nextPane, "Next Pane", "View")
	registry.register("toggle_explorer", toggleExplorer, "Toggle Explorer", "View")
	registry.register("next_diagnostic", nextDiagnostic, "Next Diagnostic", "Diagnostics")

	def listThemes(editor):
		themes = editor.theme.availableThemes()
		editor.paletteOpen = True
		editor.paletteMode = "themes"
		editor.paletteInput = ""
		editor.paletteSelection = 0
		editor.paletteItems = [
			{"name": t["name"], "command": f"__theme__{t['id']}"}
			for t in themes
		]
		editor.notifyChanged()
	
	registry.register("select_theme", listThemes, "Select Theme", "Settings")
	
	def quitEditor(editor):
		editor.saveConfig()
		editor.running = False
		try:
			from PyQt6.QtWidgets import QApplication
			QApplication.quit()
		except Exception:
			pass

	registry.register("quit", quitEditor, "Quit", "File")