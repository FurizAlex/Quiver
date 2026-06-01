class Command:
	def __init__(self, name, callback, title=None, category="General"):
		self.name = name
		self.callback = callback
		self.title = title or name
		self.category = category

class CommandRegistry:
	def __init__(self):
		self.commands = {}

	def register(self, name, callback, title=None, category="General"):
		self.commands[name] = Command(name=name, callback=callback, title=title, category=category)

	def execute(self, editor, name, *args, **kwargs):
		command = self.commands.get(name)

		if command is None:
			editor.status = f"Unknown Command: {name}"
			editor.statusTimer = 120
			return None
		if hasattr(editor, "plugins"):
			editor.plugins.dispatchCommand(editor, name)
		return command.callback(editor, *args, **kwargs)
		
	def exists(self, name):
		return name in self.commands

	def get(self, name):
		return self.commands.get(name)
		
	def list(self):
		return list(self.commands.keys())
	
	def all(self):
		return self.commands.values()