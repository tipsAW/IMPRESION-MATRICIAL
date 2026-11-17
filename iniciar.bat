@echo off
cd /d "%~dp0"
python unir_comprobantes.py
if errorlevel 1 pause
