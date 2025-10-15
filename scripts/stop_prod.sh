#!/bin/bash
# Stop production services

echo "🛑 Stopping BRI Video Agent services..."

docker-compose down

echo "✓ All services stopped"
echo ""
echo "To remove volumes (including data), run:"
echo "  docker-compose down -v"
