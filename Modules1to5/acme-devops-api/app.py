"""
DevOps Dashboard REST API

This FastAPI application provides REST endpoints for DevOps dashboard functionality,
including deployments, metrics, health checks, and logs. It serves as a standalone
API that can be consumed by MCP servers or any other HTTP client.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn
import time

from routes import deployments, metrics, health, logs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="DevOps Dashboard API",
    description="REST API for DevOps dashboard functionality including deployments, metrics, health checks, and logs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(deployments.router, prefix="/api/v1", tags=["deployments"])
app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(logs.router, prefix="/api/v1", tags=["logs"])

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests with timing information.
    
    Args:
        request: The incoming request
        call_next: The next middleware/endpoint to call
        
    Returns:
        Response: The response from the next middleware/endpoint
    """
    start_time = time.time()
    
    # Log request details
    logger.info(f"Request: {request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")
    
    # Process the request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response details
    logger.info(f"Response: {response.status_code} - Time: {process_time:.3f}s")
    
    # Add timing header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

@app.get("/health")
async def health_check():
    """
    Simple health check endpoint for load balancers and monitoring.
    
    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "service": "devops-dashboard-api",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        dict: API information and available endpoints
    """
    return {
        "name": "DevOps Dashboard API",
        "version": "1.0.0",
        "description": "REST API for DevOps dashboard functionality",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "deployments": "/api/v1/deployments",
            "metrics": "/api/v1/metrics", 
            "health_checks": "/api/v1/health",
            "logs": "/api/v1/logs"
        }
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Handle HTTP exceptions properly.
    
    Args:
        request: The request that caused the exception
        exc: The HTTPException that was raised
        
    Returns:
        JSONResponse: Error response with details
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.
    
    Args:
        request: The request that caused the exception
        exc: The exception that was raised
        
    Returns:
        JSONResponse: Error response with details
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc) if app.debug else "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    # This allows running the app directly with python app.py
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
