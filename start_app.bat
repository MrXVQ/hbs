@echo off
echo Starting Traveler Registration System...
echo.

REM Set environment variables
set DATABASE_URL=postgresql://postgres:qwerty@localhost:5432/traveler_registration
set FLASK_APP=main.py
set FLASK_ENV=production
set SESSION_SECRET=e64dd920454190dac61dab60e6e2b42d

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Virtual environment activated.
) else (
    echo Virtual environment not found!
    pause
    exit /b
)

REM Run the application
echo Starting the application...
start /min python main.py

REM Wait for the server to start
echo Waiting for server to start...
timeout /t 3 > nul

REM Check if server is up
curl --silent --head http://127.0.0.1:5000 | findstr /i "200 OK" > nul

if %errorlevel%==0 (
    set URL=http://127.0.0.1:5000
) else (
    set URL=http://192.168.33.9:5000
)

REM Try to open in browsers manually if WHERE fails

set "FIREFOX=C:\Program Files\Mozilla Firefox\firefox.exe"
set "CHROME=C:\Program Files\Google\Chrome\Application\chrome.exe"
set "EDGE=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

if exist "%FIREFOX%" (
    echo Opening in Firefox...
    start "" "%FIREFOX%" "%URL%"
    exit /b
)

if exist "%CHROME%" (
    echo Opening in Chrome...
    start "" "%CHROME%" "%URL%"
    exit /b
)

if exist "%EDGE%" (
    echo Opening in Edge...
    start "" "%EDGE%" "%URL%"
    exit /b
)

REM None found
echo No supported browser found! Please open %URL% manually.
pause
exit /b
