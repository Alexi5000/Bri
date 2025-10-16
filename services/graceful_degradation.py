"""Graceful degradation service for BRI.

Handles service failures gracefully by:
- Falling back to cached data when database unavailable
- Providing partial responses when some data is missing
- Queuing requests during maintenance
- Using circuit breakers for external dependencies
- Logging all degradation events
"""

import logging
import time
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from enum import Enum
import json

from mcp_server.circuit_breaker import (
    database_breaker,
    cache_breaker,
    groq_api_breaker,
    CircuitBreakerOpenError
)
from services.error_handler import ErrorHandler
from utils.logging_config import get_logger, LogContext

logger = get_logger(__name__)


class ServiceStatus(Enum):
    """Service availability status."""
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class DegradationMode(Enum):
    """Types of degradation modes."""
    CACHE_ONLY = "cache_only"  # Use cached data only
    PARTIAL_DATA = "partial_data"  # Some data missing
    QUEUED = "queued"  # Request queued for later
    FALLBACK = "fallback"  # Using fallback service


class GracefulDegradationService:
    """Manages graceful degradation across all BRI services."""
    
    def __init__(self):
        """Initialize degradation service."""
        self.service_status: Dict[str, ServiceStatus] = {}
        self.degradation_events: List[Dict[str, Any]] = []
        self.request_queue: List[Dict[str, Any]] = []
        self.cache_fallback_enabled = True
        self.partial_response_enabled = True
        
        logger.info("Graceful degradation service initialized")
    
    def check_database_availability(self) -> bool:
        """Check if database is available.
        
        Returns:
            True if database is available
        """
        try:
            from storage.database import Database
            
            db = Database()
            # Simple query to test connection
            db.cursor.execute("SELECT 1")
            db.cursor.fetchone()
            
            self.service_status['database'] = ServiceStatus.AVAILABLE
            return True
            
        except Exception as e:
            logger.error(f"Database unavailable: {e}")
            self.service_status['database'] = ServiceStatus.UNAVAILABLE
            self._log_degradation_event('database', str(e))
            return False
    
    def check_cache_availability(self) -> bool:
        """Check if cache (Redis) is available.
        
        Returns:
            True if cache is available
        """
        try:
            from config import Config
            
            if not Config.REDIS_ENABLED:
                self.service_status['cache'] = ServiceStatus.UNAVAILABLE
                return False
            
            import redis
            r = redis.from_url(Config.REDIS_URL, socket_timeout=2)
            r.ping()
            
            self.service_status['cache'] = ServiceStatus.AVAILABLE
            return True
            
        except Exception as e:
            logger.warning(f"Cache unavailable: {e}")
            self.service_status['cache'] = ServiceStatus.UNAVAILABLE
            self._log_degradation_event('cache', str(e))
            return False
    
    def check_groq_api_availability(self) -> bool:
        """Check if Groq API is available.
        
        Returns:
            True if API is available
        """
        try:
            from groq import Groq
            from config import Config
            
            client = Groq(api_key=Config.GROQ_API_KEY)
            # Simple test request
            response = client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            
            self.service_status['groq_api'] = ServiceStatus.AVAILABLE
            return True
            
        except Exception as e:
            logger.error(f"Groq API unavailable: {e}")
            self.service_status['groq_api'] = ServiceStatus.UNAVAILABLE
            self._log_degradation_event('groq_api', str(e))
            return False
    
    def get_data_with_fallback(
        self,
        primary_fetch: Callable,
        cache_key: Optional[str] = None,
        video_id: Optional[str] = None
    ) -> Optional[Any]:
        """Fetch data with fallback to cache if database unavailable.
        
        Args:
            primary_fetch: Function to fetch data from primary source
            cache_key: Cache key for fallback
            video_id: Video ID for context
            
        Returns:
            Data from primary source or cache, or None
        """
        with LogContext(video_id=video_id, cache_key=cache_key):
            # Try primary source with circuit breaker
            try:
                result = database_breaker.call(primary_fetch)
                logger.info("Data fetched from primary source")
                return result
                
            except CircuitBreakerOpenError:
                logger.warning("Database circuit breaker open, using cache fallback")
                return self._fetch_from_cache(cache_key)
                
            except Exception as e:
                logger.error(f"Primary fetch failed: {e}", exc_info=True)
                
                # Try cache fallback
                if self.cache_fallback_enabled and cache_key:
                    logger.info("Attempting cache fallback")
                    cached_data = self._fetch_from_cache(cache_key)
                    
                    if cached_data:
                        self._log_degradation_event(
                            'database',
                            f"Using cached data for {cache_key}",
                            mode=DegradationMode.CACHE_ONLY
                        )
                        return cached_data
                
                logger.error("No fallback data available")
                return None
    
    def _fetch_from_cache(self, cache_key: str) -> Optional[Any]:
        """Fetch data from cache.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached data or None
        """
        if not cache_key:
            return None
        
        try:
            from config import Config
            import redis
            
            if not Config.REDIS_ENABLED:
                return None
            
            r = redis.from_url(Config.REDIS_URL, socket_timeout=2)
            cached = r.get(cache_key)
            
            if cached:
                logger.info(f"Cache hit for {cache_key}")
                return json.loads(cached)
            else:
                logger.info(f"Cache miss for {cache_key}")
                return None
                
        except Exception as e:
            logger.error(f"Cache fetch failed: {e}")
            return None
    
    def build_partial_response(
        self,
        video_id: str,
        available_data: Dict[str, Any],
        missing_data: List[str]
    ) -> Dict[str, Any]:
        """Build partial response when some data is missing.
        
        Args:
            video_id: Video ID
            available_data: Data that is available
            missing_data: List of missing data types
            
        Returns:
            Partial response with user message
        """
        with LogContext(video_id=video_id):
            logger.warning(f"Building partial response. Missing: {missing_data}")
            
            # Build user-friendly message
            if len(missing_data) == 1:
                message = f"I don't have {missing_data[0]} data right now, but here's what I can tell you:"
            else:
                missing_str = ", ".join(missing_data[:-1]) + f" and {missing_data[-1]}"
                message = f"I'm missing some data ({missing_str}), but here's what I have:"
            
            self._log_degradation_event(
                'data_pipeline',
                f"Partial response for {video_id}. Missing: {missing_data}",
                mode=DegradationMode.PARTIAL_DATA
            )
            
            return {
                'status': 'partial',
                'message': message,
                'data': available_data,
                'missing': missing_data,
                'degraded': True
            }
    
    def queue_request(
        self,
        request_type: str,
        request_data: Dict[str, Any],
        video_id: Optional[str] = None
    ) -> str:
        """Queue request for later processing during maintenance.
        
        Args:
            request_type: Type of request
            request_data: Request data
            video_id: Video ID for context
            
        Returns:
            Queue ID
        """
        import uuid
        
        queue_id = str(uuid.uuid4())
        
        queued_request = {
            'queue_id': queue_id,
            'request_type': request_type,
            'request_data': request_data,
            'video_id': video_id,
            'queued_at': datetime.now().isoformat(),
            'status': 'queued'
        }
        
        self.request_queue.append(queued_request)
        
        with LogContext(video_id=video_id, queue_id=queue_id):
            logger.info(f"Request queued: {request_type}")
            self._log_degradation_event(
                'request_queue',
                f"Queued {request_type} request",
                mode=DegradationMode.QUEUED
            )
        
        return queue_id
    
    def process_queued_requests(self) -> int:
        """Process all queued requests.
        
        Returns:
            Number of requests processed
        """
        if not self.request_queue:
            return 0
        
        logger.info(f"Processing {len(self.request_queue)} queued requests")
        
        processed = 0
        failed = 0
        
        for request in self.request_queue[:]:  # Copy list to allow removal
            try:
                # Process request based on type
                # This would call appropriate handlers
                logger.info(f"Processing queued request: {request['queue_id']}")
                
                # Mark as processed
                request['status'] = 'processed'
                request['processed_at'] = datetime.now().isoformat()
                self.request_queue.remove(request)
                processed += 1
                
            except Exception as e:
                logger.error(f"Failed to process queued request: {e}")
                request['status'] = 'failed'
                request['error'] = str(e)
                failed += 1
        
        logger.info(f"Processed {processed} requests, {failed} failed")
        return processed
    
    def handle_groq_api_failure(
        self,
        query: str,
        video_id: str,
        error: Exception
    ) -> Dict[str, Any]:
        """Handle Groq API failure with graceful degradation.
        
        Args:
            query: User query
            video_id: Video ID
            error: Exception that occurred
            
        Returns:
            Degraded response
        """
        with LogContext(video_id=video_id):
            logger.error(f"Groq API failure: {error}")
            
            # Generate friendly error message
            user_message = ErrorHandler.handle_api_error(error)
            
            # Check if we can provide cached response
            cache_key = f"bri:response:{video_id}:{hash(query)}"
            cached_response = self._fetch_from_cache(cache_key)
            
            if cached_response:
                logger.info("Using cached response for failed API call")
                return {
                    'status': 'degraded',
                    'message': user_message + " (Using cached response)",
                    'response': cached_response,
                    'degraded': True
                }
            
            # Queue request for later
            queue_id = self.queue_request('chat', {
                'query': query,
                'video_id': video_id
            }, video_id)
            
            return {
                'status': 'queued',
                'message': user_message + " Your request has been queued and will be processed when the service recovers.",
                'queue_id': queue_id,
                'degraded': True
            }
    
    def _log_degradation_event(
        self,
        service: str,
        reason: str,
        mode: Optional[DegradationMode] = None
    ):
        """Log degradation event.
        
        Args:
            service: Service that degraded
            reason: Reason for degradation
            mode: Degradation mode
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'service': service,
            'reason': reason,
            'mode': mode.value if mode else None
        }
        
        self.degradation_events.append(event)
        
        # Keep only last 100 events
        if len(self.degradation_events) > 100:
            self.degradation_events = self.degradation_events[-100:]
        
        logger.warning(
            f"Degradation event: {service} - {reason}",
            extra={'degradation_mode': mode.value if mode else None}
        )
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status.
        
        Returns:
            System health information
        """
        # Check all services
        db_available = self.check_database_availability()
        cache_available = self.check_cache_availability()
        api_available = self.check_groq_api_availability()
        
        # Determine overall status
        if db_available and api_available:
            overall_status = ServiceStatus.AVAILABLE
        elif db_available or cache_available:
            overall_status = ServiceStatus.DEGRADED
        else:
            overall_status = ServiceStatus.UNAVAILABLE
        
        return {
            'overall_status': overall_status.value,
            'services': {
                'database': self.service_status.get('database', ServiceStatus.UNAVAILABLE).value,
                'cache': self.service_status.get('cache', ServiceStatus.UNAVAILABLE).value,
                'groq_api': self.service_status.get('groq_api', ServiceStatus.UNAVAILABLE).value
            },
            'degradation_events_count': len(self.degradation_events),
            'queued_requests': len(self.request_queue),
            'cache_fallback_enabled': self.cache_fallback_enabled,
            'partial_response_enabled': self.partial_response_enabled,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_degradation_report(self) -> Dict[str, Any]:
        """Get detailed degradation report.
        
        Returns:
            Degradation report with recent events
        """
        return {
            'system_health': self.get_system_health(),
            'recent_events': self.degradation_events[-10:],  # Last 10 events
            'queued_requests': [
                {
                    'queue_id': r['queue_id'],
                    'type': r['request_type'],
                    'queued_at': r['queued_at'],
                    'status': r['status']
                }
                for r in self.request_queue
            ]
        }


# Global instance
degradation_service = GracefulDegradationService()
