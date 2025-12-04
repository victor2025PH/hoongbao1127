@echo off
echo ========================================
echo Starting Lucky Red Services
echo ========================================
echo.

echo [1/2] Starting Backend API Server...
start "Backend API" cmd /k "cd /d %~dp0api && python main.py"
timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend Dev Server...
start "Frontend Dev" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo Services starting...
echo Backend API: http://localhost:8080
echo Frontend: http://localhost:3001
echo ========================================
echo.
echo Press any key to check service status...
pause >nul

echo.
echo Checking service status...
timeout /t 5 /nobreak >nul

netstat -ano | findstr ":8080" >nul
if %errorlevel% == 0 (
    echo [OK] Backend API is running on port 8080
) else (
    echo [ERROR] Backend API is NOT running
)

netstat -ano | findstr ":3001" >nul
if %errorlevel% == 0 (
    echo [OK] Frontend is running on port 3001
) else (
    echo [ERROR] Frontend is NOT running
)

echo.
echo ========================================
echo If services are not running, check the
echo opened command windows for errors.
echo ========================================
pause
