import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
import logging

from app.core.logger import correlation_id_var

logger = logging.getLogger(__name__)

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to inject a correlation ID into the request context and response headers.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Extract from header or generate new
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
            
        # Set context variable for logger
        token = correlation_id_var.set(correlation_id)
        
        start_time = time.time()
        
        try:
            # Add correlation_id to request state so downstream logic can access it if needed
            request.state.correlation_id = correlation_id
            
            logger.info(f"Request started: {request.method} {request.url.path}")
            
            response = await call_next(request)
            
            process_time = time.time() - start_time
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Time: {process_time:.4f}s"
            )
            
            # Return correlation ID in response header
            response.headers["X-Correlation-ID"] = correlation_id
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request failed: {request.method} {request.url.path} - Time: {process_time:.4f}s", exc_info=True)
            raise
        finally:
            correlation_id_var.reset(token)
