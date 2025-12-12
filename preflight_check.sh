#!/bin/bash

# BRI Video Agent - Pre-flight Checks
# Run this before deploying to verify your environment

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}BRI Video Agent - Pre-flight Checks${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Check Docker
echo -n "Checking Docker... "
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        echo -e "${GREEN}✓ Docker is running${NC}"
        docker --version
    else
        echo -e "${RED}✗ Docker is not running${NC}"
        echo "  Please start Docker and try again"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "  Please install Docker: https://docs.docker.com/get-docker/"
    ERRORS=$((ERRORS + 1))
fi

# Check Docker Compose
echo -n "Checking Docker Compose... "
if docker compose version &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose is available${NC}"
    docker compose version | head -n 1
else
    echo -e "${RED}✗ Docker Compose is not available${NC}"
    echo "  Please install Docker Compose v2.0+"
    ERRORS=$((ERRORS + 1))
fi

# Check .env file
echo -n "Checking .env file... "
if [ -f .env ]; then
    echo -e "${GREEN}✓ .env file exists${NC}"
    
    # Check for API key
    if grep -q "GROQ_API_KEY=" .env; then
        if grep -q "your_groq_api_key_here" .env; then
            echo -e "${YELLOW}  ⚠ GROQ_API_KEY appears to be a placeholder${NC}"
            echo "  Please edit .env and add your actual Groq API key"
            WARNINGS=$((WARNINGS + 1))
        else
            API_KEY=$(grep "GROQ_API_KEY=" .env | cut -d'=' -f2 | tr -d ' "' | tr -d "'")
            if [ ${#API_KEY} -lt 10 ]; then
                echo -e "${YELLOW}  ⚠ GROQ_API_KEY seems too short${NC}"
                WARNINGS=$((WARNINGS + 1))
            else
                echo -e "${GREEN}  ✓ GROQ_API_KEY is set${NC}"
            fi
        fi
    else
        echo -e "${RED}  ✗ GROQ_API_KEY not found in .env${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${YELLOW}⚠ .env file not found${NC}"
    if [ -f .env.example ]; then
        echo "  Creating .env from .env.example..."
        cp .env.example .env
        echo -e "${GREEN}  ✓ .env created${NC}"
        echo -e "${YELLOW}  ⚠ Please edit .env and add your GROQ_API_KEY${NC}"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${RED}  ✗ .env.example not found${NC}"
        ERRORS=$((ERRORS + 1))
    fi
fi

# Check disk space
echo -n "Checking disk space... "
AVAILABLE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE" -gt 10 ]; then
    echo -e "${GREEN}✓ ${AVAILABLE}GB available${NC}"
else
    echo -e "${YELLOW}⚠ Only ${AVAILABLE}GB available${NC}"
    echo "  At least 10GB recommended"
    WARNINGS=$((WARNINGS + 1))
fi

# Check ports
echo -n "Checking port availability... "
PORTS_OK=true

if netstat -an 2>/dev/null | grep -q ":8501.*LISTEN" || lsof -i :8501 &>/dev/null; then
    echo -e "${YELLOW}⚠ Port 8501 (Streamlit) is in use${NC}"
    PORTS_OK=false
    WARNINGS=$((WARNINGS + 1))
fi

if netstat -an 2>/dev/null | grep -q ":8000.*LISTEN" || lsof -i :8000 &>/dev/null; then
    echo -e "${YELLOW}⚠ Port 8000 (MCP Server) is in use${NC}"
    PORTS_OK=false
    WARNINGS=$((WARNINGS + 1))
fi

if netstat -an 2>/dev/null | grep -q ":6379.*LISTEN" || lsof -i :6379 &>/dev/null; then
    echo -e "${YELLOW}⚠ Port 6379 (Redis) is in use${NC}"
    PORTS_OK=false
    WARNINGS=$((WARNINGS + 1))
fi

if [ "$PORTS_OK" = true ]; then
    echo -e "${GREEN}✓ All ports available (8501, 8000, 6379)${NC}"
fi

# Check memory
echo -n "Checking available memory... "
if command -v free &> /dev/null; then
    MEM_AVAILABLE=$(free -g | awk '/^Mem:/{print $7}')
    if [ "$MEM_AVAILABLE" -ge 4 ]; then
        echo -e "${GREEN}✓ ${MEM_AVAILABLE}GB available${NC}"
    else
        echo -e "${YELLOW}⚠ Only ${MEM_AVAILABLE}GB available${NC}"
        echo "  At least 4GB recommended"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${YELLOW}⚠ Cannot check memory (free command not available)${NC}"
fi

# Check internet connectivity
echo -n "Checking internet connectivity... "
if ping -c 1 -W 2 google.com &> /dev/null; then
    echo -e "${GREEN}✓ Connected${NC}"
else
    echo -e "${YELLOW}⚠ Cannot reach internet${NC}"
    echo "  Required for downloading Docker images and AI models"
    WARNINGS=$((WARNINGS + 1))
fi

# Check required files
echo -n "Checking required files... "
REQUIRED_FILES=(
    "docker-compose.yml"
    "Dockerfile.mcp"
    "Dockerfile.ui"
    "requirements.txt"
    "app.py"
    "config.py"
)

FILES_OK=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ Missing: $file${NC}"
        FILES_OK=false
        ERRORS=$((ERRORS + 1))
    fi
done

if [ "$FILES_OK" = true ]; then
    echo -e "${GREEN}✓ All required files present${NC}"
fi

# Check directories
echo -n "Checking/creating directories... "
mkdir -p data/videos data/frames data/cache data/backups logs
if [ -d "data" ] && [ -d "logs" ]; then
    echo -e "${GREEN}✓ Directories ready${NC}"
else
    echo -e "${RED}✗ Failed to create directories${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "You're ready to deploy. Run:"
    echo -e "${BLUE}  ./deploy_test.sh${NC}"
    echo ""
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Pre-flight checks completed with $WARNINGS warning(s)${NC}"
    echo ""
    echo "You can proceed, but please review the warnings above."
    echo ""
    echo "To deploy anyway, run:"
    echo -e "${BLUE}  ./deploy_test.sh${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Pre-flight checks failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "Please fix the errors above before deploying."
    echo ""
    exit 1
fi
