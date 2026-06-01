def loadTheme(editor, name):
	try:
		editor.currentTheme = name
		editor.theme.load(name)
		editor.theme.initialize()
		editor.plugins.dispatchThemeChanged(editor, name)
		editor.status = f"Theme: {name}"
		editor.statusTimer = 120
	except Exception as e:
		editor.status = f"Theme Error: {e}"