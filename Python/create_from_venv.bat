@echo off
python -m venv venv_folder
call venv\Scripts\activate
pip install -r requirements.txt
echo.
echo Virtual environment is ready. Activate it later with:
echo   venv_folder\Scripts\activate
pause