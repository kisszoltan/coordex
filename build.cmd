@echo off

python -c "import sys; print(sys.prefix)" > PYTHON_HOME
set /P PYTHON_HOME=<PYTHON_HOME
del PYTHON_HOME

set PATH=%PATH%;%PYTHON_HOME%\LocalCache\local-packages\Python311\Scripts\

pyinstaller -F coordex.py