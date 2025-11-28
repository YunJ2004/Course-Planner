@echo off
REM start.bat - Convenience script to run the Course Planner on Windows

REM This batch file launches the Python script that installs
REM dependencies and runs the Streamlit app.  It attempts to use
REM 'python' from the PATH.  If Python is not installed or is not
REM accessible, please install Python 3 and add it to your PATH.

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Use python from the environment; fallback to py -3 if available
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    where py >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo Python is not installed or not in PATH. Please install Python 3.>
        exit /b 1
    ) else (
        set PY_CMD=py -3
    )
) else (
    set PY_CMD=python
)

%PY_CMD% install_and_run.py