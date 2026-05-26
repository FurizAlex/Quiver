class Buffer:
	def __init__(self):
		self.lines = [""]

	def insert_char(self, x, y, char):
		line = self.lines[y]

		self.lines[y] = (
			line[:x] +
			char +
			line[x:]
		)

	def delete_char(self, x, y):
		line = self.lines[y]
	
		if x > 0:
			self.lines[y] = (
				line[:x - 1] +
				line[x:]
			)

	def split_line(self, x, y):
		line = self.lines[y]

		left = line[:x]
		right = line[x:]

		self.lines[y] = left
		self.lines.insert(y + 1, right)

	def merge_line(self, y):
		if y <= 0:
			return

		prev = self.lines[y - 1]
		current = self.lines[y]

		self.lines[y - 1] = prev + current
		self.lines.pop(y)