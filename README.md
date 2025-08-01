# kamal

kamal is plugin for sublime text to check syntax errors, variable errors and auto completion in python code.

## Installation

### Install via Package Control (Recommended)

1. Open the Command Palette in Sublime Text (`Ctrl+Shift+P` or `Cmd+Shift+P`).
2. Select `Package Control: Install Package`.
3. Search for `kamal` and install it.

---

## Manual installation :-

### Syntax Errors Checker :-

Open sublime Packages directory. (Preferences > Browse packages...)

For Linux
```sh
cd ~/.config/sublime-text/Packages/User
```
Then install `jedi` module with pip.
```bash
pip install jedi --target=jedi_lib
```
Then download and move `syntax_checker.py` file also in that directory.

### Auto Completion :- 

Install jedi using above method.

Then download and move `auto_completion.py` file also in that directory.

### Variable Errors Checker :- 

Open sublime Packages directory. (Preferences > Browse packages...)

For Linux
```sh
cd ~/.config/sublime-text/Packages/User
```
Then download and move `variable_checker.py` file also in that directory.
