@echo off
title Pipeline de Compilacion - FastPrint
echo ==================================================
echo   Iniciando Pipeline Automatizado desde Batch...
echo ==================================================

:: Ejecuta el pipeline usando el entorno virtual de uv
call uv run python build_pipeline.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Hubo un fallo en la compilacion del pipeline.
    pause
    exit /b %errorlevel%
)

echo.
echo ==================================================
echo   Proceso terminado de forma nativa en Windows.
echo ==================================================
pause