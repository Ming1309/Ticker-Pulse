"""
Tickers API Router
Handles ticker collection control endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import logging
import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from collectors.collector_agent import get_collector_agent

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/tickers", tags=["Ticker Collection"])

# Pydantic models
class TickerCollectionRequest(BaseModel):
    tickers: List[str] = Field(..., description="List of ticker symbols to collect", example=["AAPL", "MSFT", "GOOGL"])
    interval_seconds: Optional[int] = Field(60, description="Collection interval in seconds (minimum 30)", ge=30, le=3600)

class TickerUpdateRequest(BaseModel):
    tickers: List[str] = Field(..., description="New list of ticker symbols", example=["AAPL", "TSLA"])

class CollectionStatusResponse(BaseModel):
    is_running: bool
    active_tickers: List[str]
    collection_interval: int
    scheduler_running: bool
    next_run_time: Optional[str] = None
    job_name: Optional[str] = None
    stats: Dict

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None

def get_collector():
    """Dependency to get collector agent"""
    return get_collector_agent()

@router.get("/status", response_model=CollectionStatusResponse)
async def get_collection_status(collector=Depends(get_collector)):
    """
    Get current collection status and statistics
    
    Returns:
        CollectionStatusResponse: Current collector status
    """
    try:
        status = collector.get_status()
        return CollectionStatusResponse(**status)
    except Exception as e:
        logger.error(f"Error getting collection status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.post("/start-collection", response_model=ApiResponse)
async def start_collection(request: TickerCollectionRequest, collector=Depends(get_collector)):
    """
    Start ticker data collection
    
    Args:
        request: Collection configuration with tickers and interval
        
    Returns:
        ApiResponse: Success status and collection details
    """
    try:
        # Validate tickers
        if not request.tickers:
            raise HTTPException(status_code=400, detail="No tickers provided")
        
        # Clean and validate ticker symbols
        tickers = [ticker.strip().upper() for ticker in request.tickers if ticker.strip()]
        
        if not tickers:
            raise HTTPException(status_code=400, detail="No valid tickers provided")
        
        # Check if already running
        status = collector.get_status()
        if status['is_running']:
            raise HTTPException(
                status_code=400, 
                detail=f"Collection is already running for: {', '.join(status['active_tickers'])}"
            )
        
        # Start collection
        success = collector.start_collection(
            tickers=tickers,
            interval_seconds=request.interval_seconds
        )
        
        if success:
            new_status = collector.get_status()
            return ApiResponse(
                success=True,
                message=f"Collection started successfully for {len(tickers)} tickers",
                data={
                    "tickers": tickers,
                    "interval_seconds": request.interval_seconds,
                    "next_run_time": new_status.get("next_run_time"),
                    "stats": new_status["stats"]
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to start collection")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting collection: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/stop-collection", response_model=ApiResponse)
async def stop_collection(collector=Depends(get_collector)):
    """
    Stop ticker data collection
    
    Returns:
        ApiResponse: Success status and final statistics
    """
    try:
        # Get status before stopping
        status_before = collector.get_status()
        
        if not status_before['is_running']:
            return ApiResponse(
                success=False,
                message="Collection is not currently running",
                data={"status": "not_running"}
            )
        
        # Stop collection
        success = collector.stop_collection()
        
        if success:
            return ApiResponse(
                success=True,
                message="Collection stopped successfully",
                data={
                    "final_stats": status_before["stats"],
                    "was_collecting": status_before["active_tickers"]
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to stop collection")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping collection: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/update-tickers", response_model=ApiResponse)
async def update_active_tickers(request: TickerUpdateRequest, collector=Depends(get_collector)):
    """
    Update the list of active tickers without stopping collection
    
    Args:
        request: New ticker list
        
    Returns:
        ApiResponse: Success status and updated configuration
    """
    try:
        # Validate tickers
        if not request.tickers:
            raise HTTPException(status_code=400, detail="No tickers provided")
        
        # Clean and validate ticker symbols
        tickers = [ticker.strip().upper() for ticker in request.tickers if ticker.strip()]
        
        if not tickers:
            raise HTTPException(status_code=400, detail="No valid tickers provided")
        
        # Check if collection is running
        status = collector.get_status()
        if not status['is_running']:
            raise HTTPException(
                status_code=400, 
                detail="Cannot update tickers: collection is not running"
            )
        
        # Update tickers
        success = collector.update_tickers(tickers)
        
        if success:
            new_status = collector.get_status()
            return ApiResponse(
                success=True,
                message=f"Tickers updated successfully to: {', '.join(tickers)}",
                data={
                    "old_tickers": status["active_tickers"],
                    "new_tickers": tickers,
                    "next_run_time": new_status.get("next_run_time")
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to update tickers")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tickers: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/force-collection", response_model=ApiResponse)
async def force_immediate_collection(collector=Depends(get_collector)):
    """
    Force immediate data collection for active tickers
    
    Returns:
        ApiResponse: Collection results for each ticker
    """
    try:
        # Check if there are active tickers
        status = collector.get_status()
        if not status['active_tickers']:
            raise HTTPException(
                status_code=400, 
                detail="No active tickers to collect. Start collection first."
            )
        
        # Force collection
        results = collector.force_collection()
        
        if results:
            successful_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            return ApiResponse(
                success=True,
                message=f"Force collection completed: {successful_count}/{total_count} successful",
                data={
                    "results": results,
                    "successful_count": successful_count,
                    "failed_count": total_count - successful_count,
                    "active_tickers": status['active_tickers']
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Force collection returned no results")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in force collection: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check endpoint for ticker collection service
    
    Returns:
        dict: Service health status
    """
    try:
        collector = get_collector_agent()
        status = collector.get_status()
        
        return {
            "service": "ticker_collection",
            "status": "healthy",
            "scheduler_running": status.get("scheduler_running", False),
            "collection_active": status.get("is_running", False),
            "timestamp": status["stats"].get("last_collection_time")
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
