import importlib
import os

class PluginManager:
	def __init__(self):
		self.plugins = []

	def load(self, editor, moduleName):
		try:
			module = importlib.import_module(f"plugins.{moduleName}")
			plugin = module.Plugin()
			self.plugins.append(plugin)
			if hasattr(plugin, "onLoad"):
				plugin.onLoad(editor)
			editor.status = f"Loaded Plugin: {moduleName}"
		except Exception as e:
			editor.status = f"Plugin Error: {e}"

	def dispatch(self, method, *args):
		for plugin in self.plugins:
			handler = getattr(plugin, method, None)
			if handler:
				handler(*args)

	def dispatchKey(self, editor, event):
		self.dispatch("onKey", editor, event)

	def dispatchSave(self, editor):
		self.dispatch("onSave", editor)
	
	def dispatchOpen(self, editor, filename):
		self.dispatch("onOpen", editor, filename)

	def dispatchCommand(self, editor, command):
		self.dispatch("onCommand", editor, command)

	def dispatchBufferCreated(self, editor, buffer):
		self.dispatch("onBufferCreated", editor, buffer)

	def dispatchBufferClosed(self, editor, buffer):
		self.dispatch("onBufferClosed", editor, buffer)

	def dispatchThemeChanged(self, editor, theme):
		self.dispatch("onThemeChanged", editor, theme)