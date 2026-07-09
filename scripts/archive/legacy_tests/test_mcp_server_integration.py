"""Integration test for MCP server endpoints."""

import sys
import os
import time
import logging
from multiprocessing import Process

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def start_server():
    """Start the MCP server in a separate process."""
    import uvicorn
    from mcp_server.main import app
    
    # Use a different port for testing to avoid conflicts
    uvicorn.run(
        app,
        host="localhost",
        port=8765,
        log_level="error"
    )


def test_endpoints():
    """Test MCP server endpoints."""
    import requests
    
    # Use test port
    base_url = "http://localhost:8765"
    
    logger.info(f"Testing MCP server at {base_url}")
    
    # Wait for server to start
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                logger.info("✓ Server is running")
                break
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                time.sleep(1)
            else:
                logger.error("✗ Server failed to start")
                return False
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "running", f"Expected status 'running', got {data.get('status')}"
        logger.info(f"✓ Root endpoint: {data['name']} v{data['version']}")
    except Exception as e:
        logger.error(f"✗ Root endpoint failed: {str(e)}", exc_info=True)
        return False
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        logger.info(f"✓ Health endpoint: {data['tools_registered']} tools registered")
    except Exception as e:
        logger.error(f"✗ Health endpoint failed: {str(e)}")
        return False
    
    # Test tools listing
    try:
        response = requests.get(f"{base_url}/tools")
        assert response.status_code == 200
        data = response.json()
        tools = data["tools"]
        assert len(tools) == 4
        logger.info(f"✓ Tools endpoint: {len(tools)} tools available")
        for tool in tools:
            logger.info(f"  - {tool['name']}: {tool['description']}")
    except Exception as e:
        logger.error(f"✗ Tools endpoint failed: {str(e)}")
        return False
    
    # Test cache stats
    try:
        response = requests.get(f"{base_url}/cache/stats")
        assert response.status_code == 200
        data = response.json()
        logger.info(f"✓ Cache stats endpoint: enabled={data['enabled']}")
    except Exception as e:
        logger.error(f"✗ Cache stats endpoint failed: {str(e)}")
        return False
    
    logger.info("\n✓ All endpoint tests passed!")
    return True


def main():
    """Run integration tests."""
    logger.info("=" * 60)
    logger.info("MCP Server Integration Tests")
    logger.info("=" * 60 + "\n")
    
    # Start server in separate process
    server_process = Process(target=start_server)
    server_process.start()
    
    try:
        # Run tests
        success = test_endpoints()
        
        if success:
            logger.info("\n" + "=" * 60)
            logger.info("All integration tests passed!")
            logger.info("=" * 60)
            sys.exit(0)
        else:
            logger.error("\n" + "=" * 60)
            logger.error("Some integration tests failed!")
            logger.error("=" * 60)
            sys.exit(1)
    finally:
        # Stop server
        server_process.terminate()
        server_process.join(timeout=5)
        if server_process.is_alive():
            server_process.kill()
        logger.info("\nServer stopped")


if __name__ == "__main__":
    main()
