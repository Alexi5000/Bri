"""Process a video to prepare it for evaluation tests."""
import asyncio
import httpx
from config import Config

async def process_video(video_id: str):
    """Process a video with all tools."""
    mcp_url = Config.get_mcp_server_url()
    
    print(f"Processing video {video_id}...")
    print(f"MCP Server: {mcp_url}")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Process video with all tools
        response = await client.post(
            f"{mcp_url}/videos/{video_id}/process",
            json={"tools": None}  # None means all tools
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nProcessing complete!")
            print(f"Status: {result['status']}")
            print(f"Execution time: {result['execution_time']:.2f}s")
            print(f"\nResults:")
            for tool_name, tool_result in result.get('results', {}).items():
                cached = " (cached)" if tool_result.get('cached') else ""
                print(f"  - {tool_name}: SUCCESS{cached}")
            
            if result.get('errors'):
                print(f"\nErrors:")
                for tool_name, error in result['errors'].items():
                    print(f"  - {tool_name}: {error}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python process_test_video.py <video_id>")
        print("\nExample: python process_test_video.py test-video-123")
        sys.exit(1)
    
    video_id = sys.argv[1]
    asyncio.run(process_video(video_id))
