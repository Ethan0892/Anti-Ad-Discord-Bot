@echo off
REM Anti-Ad Bot - Complete Startup Script
REM Starts both the Discord bot and web server

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║          Anti-Ad Bot - Starting All Services              ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check if running from correct directory
if not exist "src\bot.py" (
    echo ERROR: Run this script from the Anti-Ad project root directory
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Checking dependencies...
pip install -q -r requirements.txt

REM Start bot in new window
echo Starting Discord Bot...
start "Anti-Ad Bot" cmd /k "python src/bot.py"

REM Wait a moment for bot to start
timeout /t 2 /nobreak

REM Start web server in new window
echo Starting Web Server (http://localhost:5000)...
start "Anti-Ad Web Server" cmd /k "python web_server.py"

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                    ✅ Services Started                     ║
echo ╠════════════════════════════════════════════════════════════╣
echo ║ 🤖 Discord Bot   → Running in first window                ║
echo ║ 🌐 Web Server    → http://localhost:5000                  ║
echo ║ 📚 Documentation → docs/WEB_INTERFACE_GUIDE.md            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
pause
