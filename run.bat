@echo off
title BrandCraft AI
cd /d "%~dp0"
set PY=
where py >nul 2>nul && set PY=py -3
if "%PY%"=="" where python >nul 2>nul && set PY=python
if "%PY%"=="" (
  echo Python is not installed. Install it from https://www.python.org/downloads/ and tick "Add Python to PATH".
  pause
  exit /b
)
echo Installing requirements (first run only, needs internet)...
%PY% -m pip install --disable-pip-version-check -q -r requirements.txt
echo Starting the app...
%PY% launch.py
pause
