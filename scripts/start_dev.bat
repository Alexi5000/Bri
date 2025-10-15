@echo off
REM Development startup script for BRI Video Agent (Windows)

echo Starting BRI Video Agent (Development Mode)
echo ==============================================

REM Check if .env file exists
if not exist .env (
    echo Warning: .env file not found. Creating from .env.example...
    if exist .env.example (
        copy .env.example .env
        echo Created .env file. Please edit it with your API keys.
        echo Required: GROQ_API_KEY
        exit /b 1
    ) else (
        echo Error: .env.example not found. Please create .env manually.
        exit /b 1
    )
)

echo Environment variables loaded

REM Create necessary directories
echo Creating data directories...
if not exist data\videos mkdir data\videos
if not exist data\frames mkdir data\frames
if not exist data\cache mkdir data\cache
if not exist logs mkdir logs
echo Directories created

REM Initialize database
echo Initializing database...
python scripts\init_db.py
if errorlevel 1 (
    echo Error: Database initialization failed
    exit /b 1
)
echo Database initialized

REM Check if Redis is running (optional)
echo Checking Redis connection...
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo Warning: Redis is not running. Caching will be disabled.
) else (
    echo Redis is running
)

REM Start MCP server in background
echo Starting MCP Server...
start /B python mcp_server\main.py
timeout /t 5 /nobreak >nul

REM Wait for MCP server to be ready
echo Waiting for MCP Server to be ready...
for /L %%i in (1,1,30) do (
    curl -s http://localhost:8000/health >nul 2>&1
    if not errorlevel 1 (
        echo MCP Server is ready
        goto :mcp_ready
    )
    timeout /t 1 /nobreak >nul
)
echo Error: MCP Server failed to start
exit /b 1

:mcp_ready
REM Start Streamlit UI
echo Starting Streamlit UI...
echo ==============================================
echo BRI will be available at: http://localhost:8501
echo MCP Server running at: http://localhost:8000
echo ==============================================
echo.
echo Press Ctrl+C to stop all services
echo.

streamlit run app.py
