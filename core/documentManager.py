from core.buffer import Buffer

class DocumentManager:
	def __init__(self, editor, languageRegistry):
		self.editor = editor
		self.languageRegistry = languageRegistry
		self.buffers = [Buffer(editor=self.editor, language=languageRegistry.get("text"))]
		self.current = 0

	@property
	def active(self):
		return self.buffers[self.current]

	def next(self):
		if not self.buffers:
			return
		self.current = (self.current + 1) % len(self.buffers)

	def previous(self):
		if not self.buffers:
			return
		self.current = (self.current - 1) % len(self.buffers)

	def add(self, buffer):
		self.buffers.append(buffer)
		self.current = len(self.buffers) - 1

	def close(self):
		if len(self.buffers) <= 1:
			return False
		self.buffers.pop(self.current)
		self.current = min(self.current, len(self.buffers) - 1)
		return True