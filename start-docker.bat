@echo off
title Agent 3000 - Docker Startup

echo ===================================
echo   Agent 3000 - Docker Mode
echo ===================================
echo.

echo [1/4] Stopping old containers...
docker compose -f "%~dp0docker-compose.yml" down 2>nul

echo.
echo [2/4] Starting Ollama + Agent 3000 containers...
docker compose -f "%~dp0docker-compose.yml" up -d

echo.
echo [3/4] Waiting for Ollama to be healthy...
echo This may take 30-60 seconds on first run...
for /L %%i in (1,1,60) do (
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if %errorlevel% equ 0 (
        echo Ollama is ready!
        goto :check_model
    )
    timeout /t 1 >nul
)
echo Warning: Ollama health check timed out. Checking anyway...

:check_model
echo.
echo [4/4] Checking if llama3.2 is available...
docker exec ollama ollama list | findstr llama3.2 >nul
if %errorlevel% neq 0 (
    echo llama3.2 not found. Pulling it now...
    docker exec -it ollama ollama pull llama3.2
) else (
    echo llama3.2 model found.
)

echo.
echo ===================================
echo   All services running!
echo   App: http://localhost:8502
echo   Ollama API: http://localhost:11434
echo ===================================
echo.
echo Press any key to open the browser...
start http://localhost:8502
pause >nul