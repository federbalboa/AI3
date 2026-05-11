@echo off
title Agent 3000 - Diagnostics

echo ====================================
echo   Agent 3000 - Connection Check
echo ====================================
echo.

echo [1] Docker Status:
docker info >nul 2>&1
if %errorlevel% equ 0 (
    echo   OK: Docker is running
) else (
    echo   FAIL: Docker is not running
)
echo.

echo [2] Ollama Containers:
docker ps -a --filter "name=ollama" --format "table {{.Names}}\t{{.Status}}"
echo.

echo [3] Ollama API - localhost:
curl -s -o nul -w "   HTTP Status: %%{http_code}\n" http://localhost:11434/api/tags
echo.

echo [4] Ollama API - host.docker.internal:
curl -s -o nul -w "   HTTP Status: %%{http_code}\n" http://host.docker.internal:11434/api/tags
echo.

echo [5] Models in Ollama:
for /f "delims=" %%a in ('curl -s http://localhost:11434/api/tags 2^>nul') do (
    echo   %%a
)
echo.

echo [6] .env Configuration:
findstr "LLM_TYPE" "%~dp0.env"
findstr "OLLAMA_BASE_URL" "%~dp0.env"
findstr "OLLAMA_MODEL" "%~dp0.env"
echo.

echo ====================================
echo   Recommendations:
echo   - Run start.bat to start Ollama + Agent 3000
echo   - Or use Gemini: change LLM_TYPE='gemini' in .env
echo ====================================
echo.
pause