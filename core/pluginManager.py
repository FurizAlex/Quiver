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
			self.dispatch("onLoad", editor)
			editor.status = f"Loaded Plugin: {moduleName}"
		except Exception as e:
			editor.status = f"Plugin Error: {e}"

	def dispatchKey(self, editor, event):
		for plugin in self.plugins:
			plugin.onKey(editor, event)
	
	def dispatchSave(self, editor):
		for plugin in self.plugins:
			plugin.onSave(editor)

	def dispatchOpen(self, editor, filename):
		for plugin in self.plugins:
			plugin.onOpen(editor, filename)

	def dispatchCommand(self, editor, command):
		for plugin in self.plugins:
			plugin.onCommand(editor, command)

	def dispatchBufferCreated(self, editor, buffer):
		for plugin in self.plugins:
			plugin.onBufferCreated(editor, buffer)
	
	def dispatchBufferClosed(self, editor, buffer):
		for plugin in self.plugins:
			plugin.onBufferClosed(editor, buffer)

	def dispatchThemeChanged(self, editor, theme):
		for plugin in self.plugins:
			plugin.onThemeChanged(editor, theme)