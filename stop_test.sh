#!/bin/bash

# BRI Video Agent - Stop Test Deployment Script

set -e

echo "======================================"
echo "BRI Video Agent - Stop Deployment"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Stop and remove containers
echo "Stopping services..."
if docker compose down; then
    echo -e "${GREEN}✓ Services stopped successfully${NC}"
else
    echo -e "${RED}✗ Failed to stop services${NC}"
    exit 1
fi

echo ""
echo "======================================"
echo "Options"
echo "======================================"
echo ""
echo "To also remove volumes (WARNING: This will delete all data):"
echo "  docker compose down -v"
echo ""
echo "To view remaining containers:"
echo "  docker compose ps -a"
echo ""
echo "To clean up Docker system:"
echo "  docker system prune"
echo ""
