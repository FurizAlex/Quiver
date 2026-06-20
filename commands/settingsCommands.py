SETTINGS_TOGGLES = [
	("git_diff_enabled", "Git Diff Indicators"),
	("theme_transitions_enabled", "Theme Transition Animation"),
	("bracket_auto_remove_enabled", "Bracket Auto-Remove [CODE FILES]"),
	("session_restore_enabled", "Restore Session on Launch"),
	("cursor_trail_enabled", "Cursor Motion Trail"),
	("auto_pairs", "Auto-Close Brackets/Quotes"),
	("relative_numbers", "Relative Line Numbers"),
	("wrap_text", "Wrap Text"),
]

def listSettings(editor, preserveSelection=True):
	editor.paletteOpen = True
	editor.paletteMode = "settings"
	editor.paletteInput = ""
	if not preserveSelection:
		editor.paletteSelection = 0
	items = []
	for key, label in SETTINGS_TOGGLES:
		current = editor.settings.get(key, True)
		status = "ON" if current else "OFF"
		items.append({
			"name": f"{label} [{status}]",
			"command": f"__setting__{key}",
		})
	editor.paletteItems = items
	editor.notifyChanged()