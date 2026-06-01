class Command:
	def __init__(self, name, callback):
		self.name = name
		self.callback = callback

class CommandRegistry:
	def __init__(self):
		self.commands = {}

	def register(self, name, callback):
		self.commands[name] = Command(name, callback)

	def execute(self, editor, name, *args, **kwargs):
		command = self.commands.get(name)

		if not command:
			editor.status = f"Unknown Command: {name}"
			editor.statusTimer = 120
			return
		return command.callback(editor, *args, **kwargs)
		
	def exists(self, name):
		return name in self.commands
		
	def list(self):
		return list(self.commands.keys())