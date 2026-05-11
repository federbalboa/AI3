@echo off
title Agent 3000
echo =======================================
echo Iniciando Agent 3000...
echo =======================================
echo.

:: Opcional: Si usas un entorno virtual, descomenta la linea de abajo
:: call venv\Scripts\activate

echo Levantando aplicacion Streamlit...
python -m streamlit run app.py

pause
