#!/bin/bash
# Production startup script for BRI Video Agent using Docker Compose

set -e

echo "🚀 Starting BRI Video Agent (Production Mode)"
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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "✗ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "✗ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"

# Build and start services
echo "🐳 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
for i in {1..60}; do
    if docker-compose ps | grep -q "healthy"; then
        echo "✓ Services are ready"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "✗ Services failed to start. Check logs with: docker-compose logs"
        exit 1
    fi
    sleep 2
done

# Initialize database in container
echo "🗄️  Initializing database..."
docker-compose exec -T mcp-server python scripts/init_docker_db.py

echo "=============================================="
echo "✓ BRI Video Agent is running!"
echo "=============================================="
echo "📺 Streamlit UI: http://localhost:8501"
echo "🔧 MCP Server: http://localhost:8000"
echo "🗄️  Redis: localhost:6379"
echo "=============================================="
echo ""
echo "Useful commands:"
echo "  View logs:        docker-compose logs -f"
echo "  Stop services:    docker-compose down"
echo "  Restart services: docker-compose restart"
echo "  View status:      docker-compose ps"
echo ""
