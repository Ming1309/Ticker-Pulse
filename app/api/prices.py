"""
Prices API Router
Handles price data query endpoints
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
import logging
import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from app.db.base import SessionLocal
from app.db.models import Price, Ticker

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/prices", tags=["Price Data"])

# Pydantic models
class PriceData(BaseModel):
    symbol: str
    timestamp: datetime
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None
    created_at: datetime

class LatestPriceResponse(BaseModel):
    symbol: str
    price: Optional[float]
    timestamp: datetime
    change_24h: Optional[float] = None
    change_24h_percent: Optional[float] = None

class PriceHistoryResponse(BaseModel):
    symbol: str
    period: str
    data_points: int
    prices: List[PriceData]

class PriceSummaryResponse(BaseModel):
    symbol: str
    latest_price: Optional[float]
    high_24h: Optional[float]
    low_24h: Optional[float]
    volume_24h: Optional[float]
    price_change_24h: Optional[float]
    price_change_percent_24h: Optional[float]
    first_recorded: Optional[datetime]
    last_updated: Optional[datetime]
    total_records: int

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

# Database dependency
def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/latest", response_model=List[LatestPriceResponse])
async def get_latest_prices(
    tickers: Optional[str] = Query(None, description="Comma-separated ticker symbols (e.g., 'AAPL,MSFT')"),
    db: Session = Depends(get_db)
):
    """
    Get latest prices for specified tickers or all active tickers
    
    Args:
        tickers: Optional comma-separated ticker symbols
        
    Returns:
        List[LatestPriceResponse]: Latest price data for each ticker
    """
    try:
        # Parse ticker symbols
        if tickers:
            ticker_list = [t.strip().upper() for t in tickers.split(',') if t.strip()]
        else:
            # Get all active tickers from database
            active_tickers = db.query(Ticker.symbol).filter(Ticker.is_active == True).all()
            ticker_list = [t.symbol for t in active_tickers]
        
        if not ticker_list:
            return []
        
        latest_prices = []
        
        for symbol in ticker_list:
            # Get latest price record
            latest_price = (
                db.query(Price)
                .filter(Price.symbol == symbol)
                .order_by(desc(Price.ts))
                .first()
            )
            
            if latest_price:
                # Calculate 24h change if possible
                change_24h = None
                change_24h_percent = None
                
                # Get price from 24 hours ago
                yesterday = latest_price.ts - timedelta(hours=24)
                old_price = (
                    db.query(Price)
                    .filter(
                        and_(
                            Price.symbol == symbol,
                            Price.ts >= yesterday,
                            Price.ts < latest_price.ts
                        )
                    )
                    .order_by(Price.ts)
                    .first()
                )
                
                if old_price and old_price.close and latest_price.close:
                    change_24h = latest_price.close - old_price.close
                    change_24h_percent = (change_24h / old_price.close) * 100
                
                latest_prices.append(LatestPriceResponse(
                    symbol=symbol,
                    price=latest_price.close,
                    timestamp=latest_price.ts,
                    change_24h=change_24h,
                    change_24h_percent=change_24h_percent
                ))
            else:
                # No data available for this ticker
                latest_prices.append(LatestPriceResponse(
                    symbol=symbol,
                    price=None,
                    timestamp=datetime.now()
                ))
        
        return latest_prices
        
    except Exception as e:
        logger.error(f"Error getting latest prices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get latest prices: {str(e)}")

@router.get("/history/{symbol}", response_model=PriceHistoryResponse)
async def get_price_history(
    symbol: str,
    hours: Optional[int] = Query(24, description="Number of hours of history (default: 24)", ge=1, le=168),
    limit: Optional[int] = Query(100, description="Maximum number of records (default: 100)", ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get price history for a specific ticker
    
    Args:
        symbol: Ticker symbol
        hours: Number of hours of history to retrieve
        limit: Maximum number of records to return
        
    Returns:
        PriceHistoryResponse: Historical price data
    """
    try:
        symbol = symbol.upper()
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Query price history
        price_records = (
            db.query(Price)
            .filter(
                and_(
                    Price.symbol == symbol,
                    Price.ts >= start_time,
                    Price.ts <= end_time
                )
            )
            .order_by(desc(Price.ts))
            .limit(limit)
            .all()
        )
        
        # Convert to response format
        prices = []
        for record in price_records:
            prices.append(PriceData(
                symbol=record.symbol,
                timestamp=record.ts,
                open=record.open,
                high=record.high,
                low=record.low,
                close=record.close,
                volume=record.volume,
                created_at=record.created_at
            ))
        
        return PriceHistoryResponse(
            symbol=symbol,
            period=f"{hours}h",
            data_points=len(prices),
            prices=prices
        )
        
    except Exception as e:
        logger.error(f"Error getting price history for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get price history: {str(e)}")

@router.get("/summary/{symbol}", response_model=PriceSummaryResponse)
async def get_price_summary(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Get price summary statistics for a ticker
    
    Args:
        symbol: Ticker symbol
        
    Returns:
        PriceSummaryResponse: Price summary with 24h statistics
    """
    try:
        symbol = symbol.upper()
        
        # Get latest price
        latest_price = (
            db.query(Price)
            .filter(Price.symbol == symbol)
            .order_by(desc(Price.ts))
            .first()
        )
        
        if not latest_price:
            raise HTTPException(status_code=404, detail=f"No data found for ticker: {symbol}")
        
        # Get 24h statistics
        yesterday = datetime.now() - timedelta(hours=24)
        
        # Get 24h high, low, volume
        stats_24h = (
            db.query(
                func.max(Price.high).label('high_24h'),
                func.min(Price.low).label('low_24h'),
                func.sum(Price.volume).label('volume_24h')
            )
            .filter(
                and_(
                    Price.symbol == symbol,
                    Price.ts >= yesterday
                )
            )
            .first()
        )
        
        # Get 24h price change
        old_price = (
            db.query(Price)
            .filter(
                and_(
                    Price.symbol == symbol,
                    Price.ts >= yesterday,
                    Price.ts < latest_price.ts
                )
            )
            .order_by(Price.ts)
            .first()
        )
        
        price_change_24h = None
        price_change_percent_24h = None
        
        if old_price and old_price.close and latest_price.close:
            price_change_24h = latest_price.close - old_price.close
            price_change_percent_24h = (price_change_24h / old_price.close) * 100
        
        # Get first and last record timestamps
        first_record = (
            db.query(Price.created_at)
            .filter(Price.symbol == symbol)
            .order_by(Price.created_at)
            .first()
        )
        
        # Get total record count
        total_records = db.query(Price).filter(Price.symbol == symbol).count()
        
        return PriceSummaryResponse(
            symbol=symbol,
            latest_price=latest_price.close,
            high_24h=stats_24h.high_24h if stats_24h else None,
            low_24h=stats_24h.low_24h if stats_24h else None,
            volume_24h=stats_24h.volume_24h if stats_24h else None,
            price_change_24h=price_change_24h,
            price_change_percent_24h=price_change_percent_24h,
            first_recorded=first_record.created_at if first_record else None,
            last_updated=latest_price.created_at,
            total_records=total_records
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting price summary for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get price summary: {str(e)}")

@router.get("/tickers", response_model=ApiResponse)
async def get_available_tickers(db: Session = Depends(get_db)):
    """
    Get list of all available tickers with data
    
    Returns:
        ApiResponse: List of available tickers with metadata
    """
    try:
        # Get all tickers with their latest prices
        ticker_data = (
            db.query(
                Ticker.symbol,
                Ticker.is_active,
                Ticker.created_at,
                func.count(Price.id).label('record_count'),
                func.max(Price.ts).label('last_update')
            )
            .outerjoin(Price, Ticker.symbol == Price.symbol)
            .group_by(Ticker.symbol, Ticker.is_active, Ticker.created_at)
            .all()
        )
        
        tickers = []
        for ticker in ticker_data:
            tickers.append({
                "symbol": ticker.symbol,
                "is_active": ticker.is_active,
                "created_at": ticker.created_at,
                "record_count": ticker.record_count,
                "last_update": ticker.last_update
            })
        
        return ApiResponse(
            success=True,
            message=f"Found {len(tickers)} tickers",
            data={
                "tickers": tickers,
                "total_count": len(tickers),
                "active_count": sum(1 for t in tickers if t["is_active"])
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting available tickers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tickers: {str(e)}")

@router.delete("/data/{symbol}", response_model=ApiResponse)
async def delete_ticker_data(
    symbol: str,
    confirm: bool = Query(False, description="Set to true to confirm deletion"),
    db: Session = Depends(get_db)
):
    """
    Delete all price data for a specific ticker
    
    Args:
        symbol: Ticker symbol to delete
        confirm: Must be true to perform deletion
        
    Returns:
        ApiResponse: Deletion result
    """
    try:
        if not confirm:
            raise HTTPException(
                status_code=400, 
                detail="Set confirm=true to perform deletion"
            )
        
        symbol = symbol.upper()
        
        # Count records before deletion
        record_count = db.query(Price).filter(Price.symbol == symbol).count()
        
        if record_count == 0:
            raise HTTPException(status_code=404, detail=f"No data found for ticker: {symbol}")
        
        # Delete price records
        deleted_prices = db.query(Price).filter(Price.symbol == symbol).delete()
        
        # Mark ticker as inactive
        ticker = db.query(Ticker).filter(Ticker.symbol == symbol).first()
        if ticker:
            ticker.is_active = False
            ticker.updated_at = datetime.now()
        
        db.commit()
        
        return ApiResponse(
            success=True,
            message=f"Successfully deleted {deleted_prices} price records for {symbol}",
            data={
                "symbol": symbol,
                "deleted_records": deleted_prices,
                "ticker_deactivated": bool(ticker)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete data: {str(e)}")

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for price data service
    
    Returns:
        dict: Service health status
    """
    try:
        # Test database connectivity
        total_records = db.query(Price).count()
        total_tickers = db.query(Ticker).count()
        
        return {
            "service": "price_data",
            "status": "healthy",
            "database_connected": True,
            "total_price_records": total_records,
            "total_tickers": total_tickers,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Price service health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
