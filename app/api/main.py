"""
FastAPI App with CollectorAgent Integration
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from collectors.collector_agent import get_collector_agent
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MarketPulse API",
    description="Stock ticker data collection and query system",
    version="1.0.0"
)

# Pydantic models
class TickerList(BaseModel):
    tickers: List[str]
    interval_seconds: Optional[int] = 60

class CollectionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

# Get global collector agent
collector_agent = get_collector_agent()

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "MarketPulse API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "collector_status": "/api/collector/status",
            "start_collection": "/api/collector/start",
            "stop_collection": "/api/collector/stop",
            "force_collection": "/api/collector/force"
        }
    }

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "MarketPulse"}

@app.get("/api/collector/status", response_model=CollectionResponse)
def get_collector_status():
    """Get current collector status"""
    try:
        status = collector_agent.get_status()
        return CollectionResponse(
            success=True,
            message="Status retrieved successfully",
            data=status
        )
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/collector/start", response_model=CollectionResponse)
def start_collection(request: TickerList):
    """Start ticker data collection"""
    try:
        if not request.tickers:
            raise HTTPException(status_code=400, detail="No tickers provided")
        
        # Validate tickers
        tickers = [ticker.strip().upper() for ticker in request.tickers if ticker.strip()]
        
        if not tickers:
            raise HTTPException(status_code=400, detail="No valid tickers provided")
        
        # Start collection
        success = collector_agent.start_collection(
            tickers=tickers,
            interval_seconds=request.interval_seconds
        )
        
        if success:
            status = collector_agent.get_status()
            return CollectionResponse(
                success=True,
                message=f"Collection started for {len(tickers)} tickers",
                data={
                    "tickers": tickers,
                    "interval_seconds": request.interval_seconds,
                    "status": status
                }
            )
        else:
            return CollectionResponse(
                success=False,
                message="Failed to start collection"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/collector/stop", response_model=CollectionResponse)
def stop_collection():
    """Stop ticker data collection"""
    try:
        success = collector_agent.stop_collection()
        
        if success:
            return CollectionResponse(
                success=True,
                message="Collection stopped successfully"
            )
        else:
            return CollectionResponse(
                success=False,
                message="Failed to stop collection or collection was not running"
            )
            
    except Exception as e:
        logger.error(f"Error stopping collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/collector/force", response_model=CollectionResponse)
def force_collection():
    """Force immediate data collection"""
    try:
        results = collector_agent.force_collection()
        
        if results:
            successful_count = sum(1 for success in results.values() if success)
            return CollectionResponse(
                success=True,
                message=f"Force collection completed: {successful_count}/{len(results)} successful",
                data={"results": results}
            )
        else:
            return CollectionResponse(
                success=False,
                message="No active tickers or force collection failed"
            )
            
    except Exception as e:
        logger.error(f"Error in force collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("🚀 MarketPulse API starting up...")
    logger.info("📊 CollectorAgent initialized and ready")

# Shutdown event
@app.on_event("shutdown")  
async def shutdown_event():
    """Application shutdown"""
    logger.info("🛑 MarketPulse API shutting down...")
    try:
        collector_agent.stop_collection()
        collector_agent.shutdown()
        logger.info("✅ CollectorAgent shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
