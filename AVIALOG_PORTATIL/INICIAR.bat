@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>&1
cd /d "%~dp0"

rem Detecta o launcher sem usar %%errorlevel%% dentro de blocos parentizados.
where py >nul 2>&1
if not errorlevel 1 goto :run_py

where python >nul 2>&1
if not errorlevel 1 goto :run_python

echo.
echo Para abrir o Avialog, instale Python 3.9 ou superior pelo site python.org.
echo Marque a opcao "Add Python to PATH" durante a instalacao.
echo Depois execute INICIAR.bat novamente.
pause
exit /b 1

:run_py
py -3 "%~dp0server.py"
set "EXIT_CODE=%ERRORLEVEL%"
goto :finish

:run_python
python "%~dp0server.py"
set "EXIT_CODE=%ERRORLEVEL%"

:finish
if not "%EXIT_CODE%"=="0" (
  echo.
  echo O servidor encerrou com codigo %EXIT_CODE%.
)
echo.
pause
exit /b %EXIT_CODE%
