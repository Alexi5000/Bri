@echo off
echo Starting BRI Streamlit UI...
echo.

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo Warning: Virtual environment not found
)

REM Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and configure your GROQ_API_KEY
    pause
    exit /b 1
)

REM Verify GROQ_API_KEY is set
python -c "from config import Config; exit(0 if Config.GROQ_API_KEY else 1)" 2>nul
if errorlevel 1 (
    echo ERROR: GROQ_API_KEY not found in .env file!
    echo Please edit .env and add your Groq API key
    pause
    exit /b 1
)

echo Configuration verified
echo.
echo Starting Streamlit on http://localhost:8501
echo Press Ctrl+C to stop
echo.

REM Start Streamlit
streamlit run app.py

pause
