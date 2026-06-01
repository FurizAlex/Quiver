from commands.fileCommands import save
from commands.fileCommands import openFileBuffer
from commands.bufferCommands import nextBuffer, previousBuffer, closeBuffer
from commands.uiCommands import splitPane, closePane, nextPane, toggleExplorer
from commands.editCommands import undo, redo

def registerCommands(registry):
	registry.register("save_file", save)
	registry.register("next_buffer", nextBuffer)
	registry.register("previous_buffer", previousBuffer)
	registry.register("close_file", closeBuffer)
	registry.register("split_pane", splitPane)
	registry.register("close_pane", closePane)
	registry.register("next_pane", nextPane)
	registry.register("toggle_explorer", toggleExplorer)
	registry.register("undo", undo)
	registry.register("redo", redo)

	def quitEditor(editor):
		editor.running = False

	registry.register("quit", quitEditor)