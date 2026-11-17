@echo off
title Servidor Web - Unificador de Comprobantes 2x1
cd /d "%~dp0"
echo ========================================================
echo   Iniciando Servidor Web de Comprobantes 2x1
echo ========================================================
python app.py
if errorlevel 1 pause
