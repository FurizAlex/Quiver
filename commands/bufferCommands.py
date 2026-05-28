def nextBuffer(editor):
	if not editor.buffers:
		return
	editor.currentBuffer = ((editor.currentBuffer + 1) % len(editor.buffers))

def previousBuffer(editor):
	if not editor.buffers:
		return
	editor.currentBuffer = (
		(editor.currentBuffer - 1) % len(editor.buffers)
	)