from api import Plugin

class Plugin(Plugin):
	def onLoad(self, editor):
		editor.status = "Hello Plugin Loaded"

	def onKey(self, editor, event):
		if event.ctrl and event.key = "H":
			editor.status = "Hello from Plugin"