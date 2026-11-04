
@echo off
title G10 SentinelHome

cd /d "%~dp0"

echo ==========================================
echo       G10 SENTINELHOME - STARTUP
echo ==========================================

if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual...
    python -m venv .venv
)

echo Ativando ambiente...
call .venv\Scripts\activate.bat

echo Instalando dependencias...
python -m pip install --upgrade pip
pip install -r backend\requirements.txt

echo.
echo Iniciando API G10 SentinelHome...
echo Documentacao: http://127.0.0.1:8000/docs
echo.

cd backend
python -m uvicorn app.main:app --reload

pause
