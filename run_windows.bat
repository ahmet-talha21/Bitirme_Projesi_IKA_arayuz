@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3.12 -m venv .venv
  if errorlevel 1 goto :failed
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :failed
.venv\Scripts\python.exe -m ika.app
if errorlevel 1 goto :failed
exit /b 0
:failed
echo Kurulum veya baslatma basarisiz. Yukaridaki hata mesajini inceleyin.
pause
exit /b 1
