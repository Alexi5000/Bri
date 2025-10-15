#!/bin/bash
# Development startup script for BRI Video Agent

set -e

echo "🚀 Starting BRI Video Agent (Development Mode)"
echo "=============================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ Created .env file. Please edit it with your API keys."
        echo "  Required: GROQ_API_KEY"
        exit 1
    else
        echo "✗ .env.example not found. Please create .env manually."
        exit 1
    fi
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check for required environment variables
if [ -z "$GROQ_API_KEY" ]; then
    echo "✗ GROQ_API_KEY not set in .env file"
    exit 1
fi

echo "✓ Environment variables loaded"

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data/videos data/frames data/cache logs
echo "✓ Directories created"

# Initialize database
echo "🗄️  Initializing database..."
python scripts/init_db.py
echo "✓ Database initialized"

# Check if Redis is running
echo "🔍 Checking Redis connection..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✓ Redis is running"
    else
        echo "⚠️  Redis is not running. Starting Redis..."
        if command -v redis-server &> /dev/null; then
            redis-server --daemonize yes
            sleep 2
            echo "✓ Redis started"
        else
            echo "⚠️  Redis not installed. Caching will be disabled."
        fi
    fi
else
    echo "⚠️  Redis CLI not found. Caching will be disabled."
fi

# Start MCP server in background
echo "🔧 Starting MCP Server..."
python mcp_server/main.py &
MCP_PID=$!
echo "✓ MCP Server started (PID: $MCP_PID)"

# Wait for MCP server to be ready
echo "⏳ Waiting for MCP Server to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ MCP Server is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "✗ MCP Server failed to start"
        kill $MCP_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Start Streamlit UI
echo "🎨 Starting Streamlit UI..."
echo "=============================================="
echo "📺 BRI will be available at: http://localhost:8501"
echo "🔧 MCP Server running at: http://localhost:8000"
echo "=============================================="
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Trap Ctrl+C to cleanup
trap "echo ''; echo '🛑 Stopping services...'; kill $MCP_PID 2>/dev/null || true; exit 0" INT

# Start Streamlit (this will block)
streamlit run app.py

# Cleanup on exit
kill $MCP_PID 2>/dev/null || true
