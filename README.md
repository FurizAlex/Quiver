# <img src='assets/icons/quiver.svg' width=32> Quiver
Quiver is a relatively simple editor

It was created for the sole purpose of replacing vscode as my main code editor
Quiver is largely inspired by the [MS-Dos Editor](https://en.wikipedia.org/wiki/MS-DOS_Editor) & [Amiga Workbench](https://en.wikipedia.org/wiki/Amiga) in terms of UI, the editor itself is largely inspired by [Vim](https://en.wikipedia.org/wiki/Vim_(text_editor))/[Emacs](https://en.wikipedia.org/wiki/Emacs) but with CUA-Controls & a Modern GUI. The goal for this editor is to make it easy to use & completely open-source.

## Features
- Retro UI
- Embedded terminal editor
- App editor
- Modifiable Themes
- CUA-Keybinds

## To Install It
```
git clone https://github.com/FurizAlex/Quiver.git
cd Quiver
./build-and-install.sh
cd dist/Quiver
chmod +x ./Quiver
./Quiver
```
note: You may need pyinstaller or other python related packages

## Layout
```
| .quiver
├─ assets
|  ├─ background
|  ├─ fonts
|  └─ icons
├─ build
├─ commands
├─ configs
├─ core
├─ dist
├─ docs
├─ frontend
├─ input
├─ plugins
├─ syntax
├─ themes
├─ ui
└─ util
```

More will posted here, later!

<img width="2000" height="1000" alt="QuiverHeader" src="https://github.com/user-attachments/assets/1ed30eeb-f47a-4019-9337-af353dc89a74" />
