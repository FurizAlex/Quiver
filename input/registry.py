from input.insertMode import handle as handleInsert
from input.paletteMode import handle as handlePalette
from input.saveMode import handle as handleSave
from input.explorerMode import handle as handleExplorer

INPUT_HANDLERS = {
	"INSERT": handleInsert,
	"PALETTE": handlePalette,
	"SAVE": handleSave,
	"EXPLORER": handleExplorer,
}