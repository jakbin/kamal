# kamal

kamal is plugin for sublime text to check syntax errors, variable errors and auto completion in python code.

## How to use :-

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

### Variable Errors Checker :- 

Open sublime Packages directory. (Preferences > Browse packages...)

For Linux
```sh
cd ~/.config/sublime-text/Packages/User
```
Then download and move `variable_checker.py` file also in that directory.