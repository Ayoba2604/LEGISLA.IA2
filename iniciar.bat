@echo off
title LEGISLA.IA - Iniciando...

set ROOT=%~dp0
set NODE=%ROOT%node-v24.14.1-win-x64\node.exe
set UVICORN=%ROOT%venv\Scripts\uvicorn.exe

echo ========================================
echo         LEGISLA.IA - Iniciando
echo ========================================
echo. 

echo [1/2] Iniciando Backend (FastAPI)...
cd /d "%ROOT%IA"
start "LEGISLA.IA - Backend" cmd /k ""%UVICORN%" main:app --host 0.0.0.0 --port 8000"

echo [2/2] Iniciando Frontend (Vite Dev)...
cd /d "%ROOT%frontend"
start "LEGISLA.IA - Frontend" cmd /k ""%NODE%" node_modules/vite/bin/vite.js dev"

echo.
echo ========================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo ========================================
echo.
echo Feche esta janela quando quiser parar.
pause
