#!/bin/bash

# BRI Video Agent - Test Deployment Script
# This script deploys the application using Docker Compose for testing

set -e

echo "======================================"
echo "BRI Video Agent - Test Deployment"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

# Check if docker compose is available
if ! docker compose version > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker Compose is not available.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is available${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit .env and add your GROQ_API_KEY before continuing.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ .env file exists${NC}"

# Check if GROQ_API_KEY is set
if grep -q "your_groq_api_key_here" .env; then
    echo -e "${YELLOW}⚠ Warning: GROQ_API_KEY appears to be a placeholder.${NC}"
    echo -e "${YELLOW}  Please edit .env and add your actual Groq API key.${NC}"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create necessary directories
echo ""
echo "Creating necessary directories..."
mkdir -p data/videos data/frames data/cache data/backups logs
echo -e "${GREEN}✓ Directories created${NC}"

# Stop any existing containers
echo ""
echo "Stopping any existing containers..."
docker compose down 2>/dev/null || true
echo -e "${GREEN}✓ Existing containers stopped${NC}"

# Build the images
echo ""
echo "Building Docker images (this may take a few minutes on first run)..."
if docker compose build; then
    echo -e "${GREEN}✓ Docker images built successfully${NC}"
else
    echo -e "${RED}✗ Failed to build Docker images${NC}"
    exit 1
fi

# Start the services
echo ""
echo "Starting services..."
if docker compose up -d; then
    echo -e "${GREEN}✓ Services started${NC}"
else
    echo -e "${RED}✗ Failed to start services${NC}"
    exit 1
fi

# Wait for services to be healthy
echo ""
echo "Waiting for services to be healthy..."
echo "This may take 30-60 seconds..."

# Wait for Redis
echo -n "  Waiting for Redis..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    sleep 1
    counter=$((counter + 1))
    echo -n "."
done

if [ $counter -ge $timeout ]; then
    echo -e " ${RED}✗ Timeout${NC}"
    echo -e "${RED}Redis failed to start. Check logs with: docker compose logs redis${NC}"
fi

# Wait for MCP Server
echo -n "  Waiting for MCP Server..."
counter=0
while [ $counter -lt $timeout ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    sleep 2
    counter=$((counter + 2))
    echo -n "."
done

if [ $counter -ge $timeout ]; then
    echo -e " ${RED}✗ Timeout${NC}"
    echo -e "${RED}MCP Server failed to start. Check logs with: docker compose logs mcp-server${NC}"
fi

# Wait for Streamlit UI
echo -n "  Waiting for Streamlit UI..."
counter=0
while [ $counter -lt $timeout ]; do
    if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    sleep 2
    counter=$((counter + 2))
    echo -n "."
done

if [ $counter -ge $timeout ]; then
    echo -e " ${RED}✗ Timeout${NC}"
    echo -e "${RED}Streamlit UI failed to start. Check logs with: docker compose logs streamlit-ui${NC}"
fi

# Show status
echo ""
echo "======================================"
echo "Deployment Status"
echo "======================================"
docker compose ps

echo ""
echo "======================================"
echo "Access URLs"
echo "======================================"
echo -e "${GREEN}Streamlit UI:${NC}       http://localhost:8501"
echo -e "${GREEN}MCP Server:${NC}        http://localhost:8000"
echo -e "${GREEN}MCP Server Docs:${NC}   http://localhost:8000/docs"
echo -e "${GREEN}Redis:${NC}             localhost:6379"

echo ""
echo "======================================"
echo "Useful Commands"
echo "======================================"
echo "View logs:             docker compose logs -f"
echo "View specific service: docker compose logs -f streamlit-ui"
echo "Stop services:         docker compose down"
echo "Restart services:      docker compose restart"
echo "Check status:          docker compose ps"

echo ""
echo -e "${GREEN}======================================"
echo "✓ Deployment Complete!"
echo "======================================${NC}"
echo ""
echo "Open your browser and navigate to: http://localhost:8501"
echo ""
