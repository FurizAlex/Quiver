import subprocess
import os

def getDiffLines(filepath):
	if not filepath or not os.path.exists(filepath):
		return {}
	try:
		directory = os.path.dirname(os.path.abspath(filepath))
		result = subprocess.run(
			["git", "diff", "--unified=0", "--", filepath],
			cwd=directory,
			capture_output=True,
			text=True,
			timeout=2,
		)
		if result.returncode not in (0, 1):
			return {}
		diffMap = {}
		currentNewLine = None
		for line in result.stdout.split("\n"):
			if (line.startswith("@@")):
				import re
				match = re.search(r"\+(\d+)", line)
				if match:
					currentNewLine = int(match.group(1))
			elif line.startswith("+") and not line.startswith("+++"):
				if currentNewLine is not None:
					diffMap[currentNewLine] = "added"
					currentNewLine += 1
			elif line.startswith("-") and not line.startswith("---"):
				if currentNewLine is not None:
					diffMap[currentNewLine] = "removed"
		return diffMap
	except Exception:
		return {}