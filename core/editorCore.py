class EditorCore:
	def __init__(self):
		from core.documentManager import DocumentManager
		from core.history import History
		from core.commandRegistry import CommandRegistry
		from core.registerCommands import registerCommands

		self.documents = DocumentManager()
		self.history = History()
		self.commands = CommandRegistry()

		registerCommands(self.commands)
		self.running = True
		self.status = ""
		
		self.selection = Selection()
		self.clipboard = Clipboard()
		self.plugins = PluginManager()
		self.panes = [Pane(0)]
		self.activePane = 0