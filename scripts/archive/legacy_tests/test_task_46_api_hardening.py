"""Test script for Task 46: API & Integration Layer Hardening."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from mcp_server.validation import (
    RateLimiter,
    VideoIdValidator,
    RequestSizeValidator,
    ValidatedToolExecutionRequest,
    ValidatedProcessVideoRequest,
    ValidatedProgressiveProcessRequest
)
from mcp_server.response_models import (
    create_standard_response,
    create_paginated_response,
    ErrorDetail
)
from mcp_server.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    ExponentialBackoff,
    CircuitBreakerOpenError
)
from mcp_server.versioning import (
    parse_version,
    APIVersion,
    get_version_info
)


def test_rate_limiter():
    """Test rate limiter functionality."""
    print("\n=== Testing Rate Limiter ===")
    
    limiter = RateLimiter(requests_per_minute=60, burst_size=5)
    client_id = "test_client"
    
    # Should allow first 5 requests (burst)
    for i in range(5):
        assert limiter.is_allowed(client_id), f"Request {i+1} should be allowed"
    
    # 6th request should be denied
    assert not limiter.is_allowed(client_id), "Request 6 should be denied"
    
    # Check retry after
    retry_after = limiter.get_retry_after(client_id)
    assert retry_after > 0, "Should have retry after time"
    
    print(f"✓ Rate limiter working correctly (retry after: {retry_after}s)")


def test_request_validation():
    """Test request validation models."""
    print("\n=== Testing Request Validation ===")
    
    # Valid tool execution request
    try:
        req = ValidatedToolExecutionRequest(
            video_id="test_video_123",
            parameters={"interval": 2.0}
        )
        print(f"✓ Valid tool execution request: {req.video_id}")
    except Exception as e:
        print(f"✗ Failed to validate tool execution request: {e}")
    
    # Invalid video_id (path traversal)
    try:
        req = ValidatedToolExecutionRequest(
            video_id="../../../etc/passwd",
            parameters={}
        )
        print("✗ Should have rejected path traversal")
    except ValueError as e:
        print(f"✓ Rejected path traversal: {e}")
    
    # Valid process video request
    try:
        req = ValidatedProcessVideoRequest(
            tools=["extract_frames", "caption_frames"]
        )
        print(f"✓ Valid process video request: {req.tools}")
    except Exception as e:
        print(f"✗ Failed to validate process video request: {e}")
    
    # Invalid tools list (too many)
    try:
        req = ValidatedProcessVideoRequest(
            tools=["tool" + str(i) for i in range(15)]
        )
        print("✗ Should have rejected too many tools")
    except ValueError as e:
        print(f"✓ Rejected too many tools: {e}")
    
    # Valid progressive process request
    try:
        req = ValidatedProgressiveProcessRequest(
            video_path="data/videos/test.mp4"
        )
        print(f"✓ Valid progressive process request: {req.video_path}")
    except Exception as e:
        print(f"✗ Failed to validate progressive process request: {e}")
    
    # Invalid video path (wrong extension)
    try:
        req = ValidatedProgressiveProcessRequest(
            video_path="data/videos/test.txt"
        )
        print("✗ Should have rejected invalid extension")
    except ValueError as e:
        print(f"✓ Rejected invalid extension: {e}")


def test_response_models():
    """Test standardized response models."""
    print("\n=== Testing Response Models ===")
    
    # Standard success response
    response = create_standard_response(
        data={"result": "success", "count": 10},
        execution_time=0.123
    )
    assert response.success is True
    assert response.data["result"] == "success"
    assert response.metadata.execution_time == 0.123
    print(f"✓ Standard success response: {response.metadata.request_id}")
    
    # Standard error response
    error = ErrorDetail(
        code="VIDEO_NOT_FOUND",
        message="Video not found",
        suggestion="Check video ID and try again"
    )
    response = create_standard_response(
        error=error,
        execution_time=0.050
    )
    assert response.success is False
    assert response.error["code"] == "VIDEO_NOT_FOUND"
    print(f"✓ Standard error response: {response.error['message']}")
    
    # Paginated response
    items = [{"id": i, "name": f"Item {i}"} for i in range(10)]
    response = create_paginated_response(
        items=items[:5],
        page=1,
        page_size=5,
        total_items=10,
        execution_time=0.075
    )
    assert len(response.data) == 5
    assert response.pagination["total_pages"] == 2
    assert response.pagination["has_next"] is True
    print(f"✓ Paginated response: page {response.pagination['page']}/{response.pagination['total_pages']}")


def test_circuit_breaker():
    """Test circuit breaker functionality."""
    print("\n=== Testing Circuit Breaker ===")
    
    breaker = CircuitBreaker(
        name="test_service",
        failure_threshold=3,
        recovery_timeout=5.0
    )
    
    # Should start in CLOSED state
    assert breaker.state == CircuitState.CLOSED
    print(f"✓ Initial state: {breaker.state.value}")
    
    # Simulate successful calls
    def success_func():
        return "success"
    
    result = breaker.call(success_func)
    assert result == "success"
    assert breaker.failure_count == 0
    print("✓ Successful call handled correctly")
    
    # Simulate failures
    def failure_func():
        raise Exception("Service unavailable")
    
    for i in range(3):
        try:
            breaker.call(failure_func)
        except Exception:
            pass
    
    # Should be OPEN after threshold failures
    assert breaker.state == CircuitState.OPEN
    print(f"✓ Circuit opened after {breaker.failure_count} failures")
    
    # Should reject requests when OPEN
    try:
        breaker.call(success_func)
        print("✗ Should have rejected request when circuit is open")
    except CircuitBreakerOpenError as e:
        print(f"✓ Rejected request when open: {str(e)[:50]}...")
    
    # Get state info
    state = breaker.get_state()
    assert state["state"] == "open"
    assert state["failure_count"] == 3
    print(f"✓ State info: {state['name']} is {state['state']}")
    
    # Reset circuit
    breaker.reset()
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0
    print("✓ Circuit reset successfully")


def test_exponential_backoff():
    """Test exponential backoff."""
    print("\n=== Testing Exponential Backoff ===")
    
    backoff = ExponentialBackoff(
        base_delay=1.0,
        max_delay=10.0,
        multiplier=2.0,
        jitter=False
    )
    
    delays = []
    for i in range(5):
        delay = backoff.get_delay()
        delays.append(delay)
    
    # Check exponential growth
    assert delays[0] == 1.0
    assert delays[1] == 2.0
    assert delays[2] == 4.0
    assert delays[3] == 8.0
    assert delays[4] == 10.0  # Capped at max_delay
    
    print(f"✓ Exponential backoff delays: {delays}")


def test_api_versioning():
    """Test API versioning."""
    print("\n=== Testing API Versioning ===")
    
    # Parse valid versions
    v1 = parse_version("1.0")
    assert v1 == APIVersion.V1
    print(f"✓ Parsed version '1.0': {v1.value}")
    
    v1_alt = parse_version("v1")
    assert v1_alt == APIVersion.V1
    print(f"✓ Parsed version 'v1': {v1_alt.value}")
    
    # Parse invalid version
    invalid = parse_version("99.0")
    assert invalid is None
    print("✓ Rejected invalid version '99.0'")
    
    # Get version info
    info = get_version_info()
    assert "current_version" in info
    assert "supported_versions" in info
    print(f"✓ Version info: current={info['current_version']}, supported={info['supported_versions']}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Task 46: API & Integration Layer Hardening - Test Suite")
    print("=" * 60)
    
    try:
        test_rate_limiter()
        test_request_validation()
        test_response_models()
        test_circuit_breaker()
        test_exponential_backoff()
        test_api_versioning()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
