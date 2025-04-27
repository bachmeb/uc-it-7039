

```zsh
python3 --version
```
```zsh
brew list pyenv
```
```zsh
pyenv --version
```
```zsh
brew update
brew upgrade pyenv
```
```zsh
pyenv versions
```
```zsh
pyenv install --list
```
```zsh
pyenv install --list | grep 3.12
```
```zsh
pyenv install 3.12.10
```
```zsh
cat ~/.zshrc
```
```zsh
nano ~/.zshrc
```
```
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
```
```zsh
source ~/.zshrc
```
```zsh
python3 --version
```
```zsh
pyenv local 3.12.10
```
```zsh
python3 --version
```
```zsh
python3 -m venv venv
```
```zsh
ls -la venv
```
```zsh
cat venv/pyvenv.cfg
```
```zsh
source venv/bin/activate
```
```zsh
python3 --version
```
```zsh
python --version
```
```zsh
pip3 --version
```
```zsh
python3 -m pip install --upgrade pip
```
```zsh
pip install <package_name>
```
```zsh
pip install boto3 flask gunicorn rdflib SPARQLWrapper
```
```zsh
pip3 freeze > requirements.txt
```
### VS Code (macOS)
* Install Python Extension for VS Code
  * Go to Extensions
  * Click the square icon on the left sidebar (or press Cmd + Shift + X).
  * Search for: Python (The top result should be the official one by Microsoft.)
  * Install the Python extension
  * Reload VS Code (or it may prompt you automatically).
* Select Python interpreter
  * Press Cmd + Shift + P
    * Search for ➔ "Python: Select Interpreter"
  * Choose your virtual environment
    * You should see something like: .venv (Python 3.x.x) /path/to/uc-it-7039/app/venv/bin/python
    * Pick the one that points to your local venv folder inside your project.
  * Check Bottom Bar
    * In the lower left of VS Code you should now see your environment selected.
    * It will show your environment name (e.g., venv, or the Python version).

```zsh
deactivate
```

## Jena Fuseki
```
cd ~/Downloads
curl -LO https://dlcdn.apache.org/jena/binaries/apache-jena-fuseki-5.4.0.tar.gz
tar -xzf apache-jena-fuseki-5.4.0.tar.gz --strip-components=1
./fuseki-server
```

