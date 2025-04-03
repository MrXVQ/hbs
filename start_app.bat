@echo off
echo Starting Traveler Registration System...
echo.

REM Set environment variables
set DATABASE_URL=postgresql://postgres:your_password@localhost:5432/traveler_registration
set FLASK_APP=main.py
set FLASK_ENV=production
set SESSION_SECRET=your_secret_key_here

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Virtual environment activated.
) else (
    echo Warning: Virtual environment not found. Please create it with:
    echo python -m venv venv
    echo Then install required packages with:
    echo pip install flask flask-login flask-sqlalchemy flask-wtf email-validator psycopg2-binary
    pause
    exit /b
)

REM Run the application
echo Starting the application...
python main.py

REM Keep window open if there's an error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred. Press any key to exit.
    pause > nul
)