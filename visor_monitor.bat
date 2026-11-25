@echo off
title Visor de Monitor - Raiton Clone
color 0A

cd /d "%~dp0"

echo.
echo  ============================================
echo    VISOR DE MONITOR - Iniciando...
echo  ============================================
echo.

REM ============================================
REM  Buscar Python automaticamente
REM ============================================
set "PYTHON_CMD="

py --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py"
    goto :python_encontrado
)

python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto :python_encontrado
)

for %%P in (
    "%LocalAppData%\Programs\Python\Python314\python.exe"
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python310\python.exe"
    "C:\Python314\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Program Files\Python314\python.exe"
    "C:\Program Files\Python313\python.exe"
    "C:\Program Files\Python312\python.exe"
    "C:\Program Files\Python311\python.exe"
) do (
    if exist %%P (
        set "PYTHON_CMD=%%~P"
        goto :python_encontrado
    )
)

echo  [ERROR] No se encontro Python en el sistema.
echo.
echo  Instalalo desde: https://www.python.org/downloads/
echo.
pause
exit /b 1

:python_encontrado
echo  [OK] Python encontrado: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

REM ============================================
REM  Instalar dependencias si faltan
REM ============================================
echo  Comprobando dependencias (mss, PySide6)...

%PYTHON_CMD% -c "import mss" >nul 2>&1
if errorlevel 1 (
    echo  [INFO] Instalando mss...
    %PYTHON_CMD% -m pip install --quiet --no-warn-script-location mss
)

%PYTHON_CMD% -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo  [INFO] Instalando PySide6...
    %PYTHON_CMD% -m pip install --quiet --no-warn-script-location PySide6
)

%PYTHON_CMD% -c "import mss, PySide6" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Alguna dependencia no se pudo instalar.
    echo  Prueba manualmente:
    echo      %PYTHON_CMD% -m pip install mss PySide6
    echo.
    pause
    exit /b 1
)

echo  [OK] Dependencias listas.
echo.

REM ============================================
REM  Comprobar que el script existe
REM ============================================
if not exist "visor_monitor.py" (
    echo  [ERROR] No se encuentra visor_monitor.py en esta carpeta.
    echo.
    pause
    exit /b 1
)

REM ============================================
REM  Borrar log anterior
REM ============================================
if exist "error_log.txt" del /q "error_log.txt"

REM ============================================
REM  Lanzar el visor
REM ============================================
echo  Lanzando visor...
echo.
%PYTHON_CMD% visor_monitor.py

REM ============================================
REM  Mostrar log al terminar
REM ============================================
echo.
echo  ============================================
if exist "error_log.txt" (
    echo   CONTENIDO DE error_log.txt:
    echo  ============================================
    type error_log.txt
) else (
    echo   (No se genero error_log.txt)
)
echo  ============================================
echo.
pause