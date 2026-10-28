@echo off
title Document Scanner & Converter Studio
color 0A
echo ========================================================
echo       Khoi dong Document Scanner Studio (Streamlit)
echo ========================================================
echo.
echo Dang mo ung dung tren trinh duyet mac dinh...
echo.

python -m streamlit run app.py --server.headless=false

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Khong the khoi chay ung dung!
    pause
)
