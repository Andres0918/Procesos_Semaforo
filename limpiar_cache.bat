@echo off
echo Limpiando cache de Python...

REM Eliminar carpetas __pycache__
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM Eliminar archivos .pyc
del /s /q *.pyc 2>nul

echo Cache limpiado!
echo Ahora ejecuta: py gui_cuenca.py
pause
