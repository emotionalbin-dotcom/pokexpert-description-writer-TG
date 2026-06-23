@echo off
cd /d "%~dp0"
echo Generating Eldorado Listing...
python parse_final.py
pause