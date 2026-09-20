@echo off

set PROJECT_ROOT=C:\Users\mfmca\projto_ibge
set PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe
set PIPELINE=%PROJECT_ROOT%\ingestion\pipeline.py

echo ============================================================
echo PIPELINE IBGE
echo ============================================================
echo.

cd /d "%PROJECT_ROOT%"

"%PYTHON%" "%PIPELINE%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo PIPELINE CONCLUIDO COM SUCESSO
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo PIPELINE FALHOU
    echo ============================================================
)

echo.
pause