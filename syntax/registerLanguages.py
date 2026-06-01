from syntax.language import Language

def registerLanguages(registry):
	registry.register(
		Language (
			id="python",
			name="Python",
			extensions=[".py"],

			comment="#",

			indent="    ",

			keywords={
				"def",
				"class",
				"if",
				"else",
				"elif",
				"return",
				"for",
				"while",
				"import",
				"from",
				"with",
				"as",
				"try",
				"except",
				"pass",
				"in",
				"not",
				"and",
				"or"
			}
		)
	)
	registry.register(
		Language (
			id="rust",
			name="Rust",
			extensions=[".rs"],

			comment="//",

			keywords={
				"fn",
				"let",
				"mut",
				"pub",
				"impl",
				"struct",
				"enum",
				"match",
				"if",
				"else",
				"for",
				"while",
				"use",
				"mod",
				"trait",
				"return"
			}
		)
	)
	registry.register(
		Language (
			id="c",
			name="C",
			extensions=[".c", ".h"],

			comment="//",

			indent="\t",

			keywords={
				"int",
				"char",
				"size_t",
				"ssize_t",
				"double",
				"class",
				"if",
				"else",
				"return",
				"for",
				"while",
				"&&",
				"||"
			}
		)
	)