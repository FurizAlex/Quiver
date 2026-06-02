from commands.fileCommands import save
from commands.fileCommands import openFileBuffer
from commands.diagnosticCommands import nextDiagnostic
from commands.bufferCommands import nextBuffer, previousBuffer, closeBuffer
from commands.uiCommands import splitPane, closePane, nextPane, toggleExplorer
from commands.editCommands import undo, redo

def registerCommands(registry):
	registry.register("save_file", save, "Save File", "File")
	registry.register("next_buffer", nextBuffer, "Next Buffer", "Buffer")
	registry.register("previous_buffer", previousBuffer, "Previous Buffer", "Buffer")
	registry.register("close_file", closeBuffer, "Close File", "File")
	registry.register("split_pane", splitPane, "Split Pane", "View")
	registry.register("close_pane", closePane, "Close Pane", "View")
	registry.register("next_pane", nextPane, "Next Pane", "View")
	registry.register("toggle_explorer", toggleExplorer, "Toggle Explorer", "View")
	registry.register("next_diagnostic", nextDiagnostic, "Next Diagnostic", "Diagnostics")
	registry.register("undo", undo, "Undo", "Edit")
	registry.register("redo", redo, "Redo", "Edit")

	def quitEditor(editor):
		editor.saveConfig()
		editor.running = False

	registry.register("quit", quitEditor, "Quit", "File")