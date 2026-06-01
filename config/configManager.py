import json
import os

CONFIG_PATH = os.path.expanuser("~/.quiver/config.json")

class ConfigManager:
	def load(self):
		try:
			with open(CONFIG_PATH) as f:
				return json.load(f)
		except:
			return {}

	def save(self, settings):
		os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
		with open(CONFIG_PATH, "W") as f:
			json.dump(settings, f, indent=4)