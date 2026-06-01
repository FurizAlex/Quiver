class Language:
	def __init__(self, id, name, extensions, comment="#", indent="    "):
		self.id = id
		self.name = name

		self.extensions = extensions

		self.comment = comment
		self.indent = indent