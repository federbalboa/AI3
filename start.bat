@echo off
title Agent 3000 - Startup

echo ===================================
echo   Agent 3000 - Starting Services
echo ===================================
echo.

echo [1/5] Checking Docker status...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)
echo Docker is running.

echo.
echo [2/5] Stopping any existing Ollama container...
docker stop ollama >nul 2>&1
docker rm ollama >nul 2>&1

echo.
echo [3/5] Starting Ollama in Docker (port 11434)...
docker run -d --name ollama -p 11434:11434 ollama/ollama:latest
echo Ollama container started. Waiting 15 seconds for initialization...
timeout /t 15 >nul

echo.
echo [4/5] Checking Ollama API (trying both URLs)...
curl -s http://host.docker.internal:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo OK: Ollama responding at host.docker.internal:11434
    set OLLAMA_URL=http://host.docker.internal:11434
    goto :start_streamlit
)
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo OK: Ollama responding at localhost:11434
    set OLLAMA_URL=http://localhost:11434
    goto :start_streamlit
)

echo WARNING: Ollama not responding yet. Will try anyway.
set OLLAMA_URL=http://localhost:11434

:start_streamlit
echo.
echo [5/5] Updating .env with correct Ollama URL...
powershell -Command "(Get-Content '%~dp0.env') -replace 'OLLAMA_BASE_URL=.*', 'OLLAMA_BASE_URL=%OLLAMA_URL%' | Set-Content '%~dp0.env'"
echo .env updated.

echo.
echo ===================================
echo   Starting Agent 3000 Web App
echo ===================================
cd /d "%~dp0"
streamlit run app.py --server.port 8502 --browser.gatherUsageStats false