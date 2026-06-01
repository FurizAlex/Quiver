from syntax.language import Language

def registerLanguages(registry):
	registry.register(
		Language(
			"python",
			"Python",
			[".py"],
			comment="#",
			indent="   "
		)
	)
	registry.register(
		Language(
			"rust",
			"Rust",
			[".rs"],
			comment="//",
			indent="   "
		)
	)
	registry.register(
		Language(
			"c",
			"C",
			[".c", ".h"],
			comment="//",
			indent="\t"
		)
	)
	registry.register(
		Language(
			"cpp",
			"C++",
			[".cpp", ".cc", ".hpp"],
			comment="//",
			indent="\t"
		)
	)
	registry.register(
		Language(
			"javascript",
			"JavaScript",
			[".js"],
			comment="//",
			indent="   "
		)
	)
	registry.register(
		Language(
			"json",
			"Json",
			[".json"],
			comment="",
			indent="   "
		)
	)
	registry.register(
		Language(
			"text",
			"Plain Text",
			[".txt"],
		)
	)
	registry.register(
		Language(
			"pyxis",
			"Pyxis",
			[".pyx"],
			comment="#",
			indent="\t"
		)
	)