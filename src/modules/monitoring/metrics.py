def setup_metrics(app):
    """Set up metrics collection for the FastAPI app with version compatibility"""
    from prometheus_fastapi_instrumentator import Instrumentator
    from prometheus_fastapi_instrumentator.metrics import latency, requests
    import logging
    from fastapi import FastAPI, HTTPException
    import traceback
    
    logger = logging.getLogger(__name__)
    
    try:
        # Create instrumentator
        instrumentator = Instrumentator()
        
        # Add core metrics that exist in all versions
        instrumentator.add(latency(buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]))
        instrumentator.add(requests())
        
        # Try to add optional metrics if they exist in this version
        try:
            from prometheus_fastapi_instrumentator.metrics import requests_in_progress
            instrumentator.add(requests_in_progress())
            logger.info("Added requests_in_progress metric")
        except ImportError as e:
            logger.info(f"requests_in_progress metric not available: {str(e)}")
            
        try:
            from prometheus_fastapi_instrumentator.metrics import dependency_timing
            instrumentator.add(dependency_timing())
            logger.info("Added dependency_timing metric")
        except ImportError as e:
            logger.info(f"dependency_timing metric not available: {str(e)}")
            
        try:
            from prometheus_fastapi_instrumentator.metrics import cpu_usage
            instrumentator.add(cpu_usage())
            logger.info("Added cpu_usage metric")
        except ImportError as e:
            logger.info(f"cpu_usage metric not available: {str(e)}")
            
        try:
            from prometheus_fastapi_instrumentator.metrics import memory_usage
            instrumentator.add(memory_usage())
            logger.info("Added memory_usage metric")
        except ImportError as e:
            logger.info(f"memory_usage metric not available: {str(e)}")
        
        # Add error handler for metrics endpoint
        @app.exception_handler(Exception)
        async def metrics_exception_handler(request, exc):
            if request.url.path == "/metrics":
                logger.error(f"Error in metrics endpoint: {str(exc)}\n{traceback.format_exc()}")
                return HTTPException(
                    status_code=500,
                    detail="Internal server error in metrics collection"
                )
            # Let other exceptions be handled by other handlers
            raise exc
        
        # Expose metrics endpoint and instrument app
        try:
            instrumentator.instrument(app).expose(app)
            logger.info("Prometheus metrics enabled at /metrics")
        except Exception as e:
            logger.error(f"Failed to expose metrics endpoint: {str(e)}\n{traceback.format_exc()}")
            # Continue without metrics rather than crashing the application
            
        return instrumentator
        
    except Exception as e:
        # Log error but don't crash the app
        logger.error(f"Failed to set up metrics: {str(e)}\n{traceback.format_exc()}")
        # Return a dummy instrumentator that does nothing
        return Instrumentator() 