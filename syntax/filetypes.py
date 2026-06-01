import os

EXTENSIONS = {
	".py": "python",
	".rs": "rust",
	".c": "c",
	".h": "c",
	".cc": "c++",
	".cpp": "c++",
	".hpp": "c++",
	".js": "javascript",
	".json": "json",
	".html": "html",
	".css": "css",
	".md": "markdown",
	".txt": "text",

	".pyx": "pyxis"
}

def detect(filename):
	if not filename:
		return "text"

	_, ext = os.path.splitext(filename)
	return EXTENSIONS.get(ext.lower(), "text")