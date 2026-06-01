class Language:
	def __init__(self, id, name, extensions, comment="#", indent="    ", keywords=None):
		self.id = id
		self.name = name
		self.keywords = keywords or set()

		self.extensions = extensions

		self.comment = comment
		self.indent = indent
