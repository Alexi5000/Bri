"""API versioning support."""

from typing import Optional
from fastapi import Header, HTTPException, status
from enum import Enum
from utils.logging_config import get_logger

logger = get_logger(__name__)


class APIVersion(Enum):
    """Supported API versions."""
    V1 = "1.0"
    V2 = "2.0"  # Future version


# Current default version
DEFAULT_VERSION = APIVersion.V1

# Deprecated versions with sunset dates
DEPRECATED_VERSIONS = {
    # APIVersion.V1: "2025-12-31"  # Example: V1 deprecated, sunset date
}

# Minimum supported version
MIN_SUPPORTED_VERSION = APIVersion.V1


def parse_version(version_string: str) -> Optional[APIVersion]:
    """
    Parse version string to APIVersion enum.
    
    Args:
        version_string: Version string (e.g., "1.0", "v1", "1")
        
    Returns:
        APIVersion enum or None if invalid
    """
    # Normalize version string
    version_string = version_string.lower().strip()
    version_string = version_string.replace("v", "")
    
    # Try to match to enum
    for version in APIVersion:
        if version.value.startswith(version_string):
            return version
    
    return None


def get_api_version(
    accept_version: Optional[str] = Header(None, alias="Accept-Version"),
    api_version: Optional[str] = Header(None, alias="API-Version")
) -> APIVersion:
    """
    Extract and validate API version from request headers.
    
    Supports two header formats:
    - Accept-Version: 1.0
    - API-Version: 1.0
    
    Args:
        accept_version: Accept-Version header value
        api_version: API-Version header value
        
    Returns:
        Validated APIVersion enum
        
    Raises:
        HTTPException: If version is invalid or unsupported
    """
    # Try both header formats
    version_string = api_version or accept_version
    
    # Use default if no version specified
    if not version_string:
        return DEFAULT_VERSION
    
    # Parse version
    version = parse_version(version_string)
    
    if version is None:
        logger.warning(f"Invalid API version requested: {version_string}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid API version: {version_string}. Supported versions: {', '.join(v.value for v in APIVersion)}",
            headers={"X-API-Version": DEFAULT_VERSION.value}
        )
    
    # Check if version is deprecated
    if version in DEPRECATED_VERSIONS:
        sunset_date = DEPRECATED_VERSIONS[version]
        logger.warning(
            f"Deprecated API version {version.value} used. "
            f"Sunset date: {sunset_date}"
        )
        # Still allow but add warning header
        # In production, you might want to reject after sunset date
    
    return version


def version_header(version: APIVersion) -> dict:
    """
    Generate version response headers.
    
    Args:
        version: API version used
        
    Returns:
        Dictionary of headers to add to response
    """
    headers = {
        "X-API-Version": version.value,
        "X-API-Supported-Versions": ", ".join(v.value for v in APIVersion)
    }
    
    # Add deprecation warning if applicable
    if version in DEPRECATED_VERSIONS:
        sunset_date = DEPRECATED_VERSIONS[version]
        headers["Deprecation"] = "true"
        headers["Sunset"] = sunset_date
        headers["Link"] = f'<https://docs.bri-api.com/migration>; rel="deprecation"'
    
    return headers


def require_version(min_version: APIVersion):
    """
    Decorator to require minimum API version for endpoint.
    
    Args:
        min_version: Minimum required API version
        
    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(*args, version: APIVersion = DEFAULT_VERSION, **kwargs):
            # Compare version values
            if APIVersion[version.name].value < min_version.value:
                raise HTTPException(
                    status_code=status.HTTP_426_UPGRADE_REQUIRED,
                    detail=f"This endpoint requires API version {min_version.value} or higher",
                    headers=version_header(version)
                )
            return await func(*args, version=version, **kwargs)
        return wrapper
    return decorator


class VersionedResponse:
    """Helper to create version-specific responses."""
    
    @staticmethod
    def format_response(data: dict, version: APIVersion) -> dict:
        """
        Format response based on API version.
        
        Args:
            data: Response data
            version: API version
            
        Returns:
            Formatted response for the version
        """
        if version == APIVersion.V1:
            # V1 format (current)
            return data
        elif version == APIVersion.V2:
            # V2 format (future) - example of how to handle version differences
            # Could have different field names, structure, etc.
            return {
                "version": "2.0",
                "payload": data
            }
        else:
            return data


def get_version_info() -> dict:
    """
    Get information about API versions.
    
    Returns:
        Dictionary with version information
    """
    return {
        "current_version": DEFAULT_VERSION.value,
        "supported_versions": [v.value for v in APIVersion],
        "deprecated_versions": {
            v.value: sunset_date
            for v, sunset_date in DEPRECATED_VERSIONS.items()
        },
        "min_supported_version": MIN_SUPPORTED_VERSION.value,
        "version_header": "Accept-Version or API-Version",
        "documentation": "https://docs.bri-api.com/versioning"
    }
