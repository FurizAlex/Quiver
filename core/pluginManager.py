import importlib
import os

class PluginManager:
	def __init__(self):
		self.plugins = []
	
	def dispatch(self, event, *args):
		for plugin in self.plugins:
			handler = getattr(plugin, event, None)
			if callable(handler):
				handler(*args)