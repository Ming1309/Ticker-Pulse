"""
Yahoo Finance Data Collector
Collects real-time stock data from Yahoo Finance using yfinance library
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YahooCollector:
    """
    Yahoo Finance data collector for stock price information
    """
    
    def __init__(self, db_session: Session = None):
        """
        Initialize the Yahoo Finance collector
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        logger.info("YahooCollector initialized")
    
    def fetch_ticker_data(self, symbol: str) -> Optional[Dict]:
        """
        Fetch latest ticker data from Yahoo Finance
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
            
        Returns:
            Dict containing ticker data or None if error
        """
        try:
            logger.info(f"Fetching data for ticker: {symbol}")
            
            # Create yfinance Ticker object
            ticker = yf.Ticker(symbol)
            
            # Get latest 1-minute data
            hist_data = ticker.history(period="1d", interval="1m")
            
            if hist_data.empty:
                logger.warning(f"No data available for ticker: {symbol}")
                return None
            
            # Get the latest row (most recent data)
            latest_data = hist_data.iloc[-1]
            
            # Get current timestamp
            current_time = datetime.now()
            
            # Prepare data dictionary
            ticker_data = {
                'symbol': symbol.upper(),
                'ts': current_time,
                'open': float(latest_data['Open']) if not pd.isna(latest_data['Open']) else None,
                'high': float(latest_data['High']) if not pd.isna(latest_data['High']) else None,
                'low': float(latest_data['Low']) if not pd.isna(latest_data['Low']) else None,
                'close': float(latest_data['Close']) if not pd.isna(latest_data['Close']) else None,
                'volume': int(latest_data['Volume']) if not pd.isna(latest_data['Volume']) else None,
                'created_at': current_time
            }
            
            logger.info(f"Successfully fetched data for {symbol}: Close=${ticker_data['close']}")
            return ticker_data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def save_to_db(self, price_data: Dict) -> bool:
        """
        Save ticker price data to database
        
        Args:
            price_data: Dictionary containing ticker price information
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.db_session:
            logger.error("Database session not provided")
            return False
        
        try:
            # Import models here to avoid circular imports
            from app.db.models import Ticker, Price
            
            symbol = price_data['symbol']
            
            # Check if ticker exists, create if not
            ticker = self.db_session.query(Ticker).filter(
                Ticker.symbol == symbol
            ).first()
            
            if not ticker:
                logger.info(f"Creating new ticker: {symbol}")
                ticker = Ticker(
                    symbol=symbol,
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                self.db_session.add(ticker)
                self.db_session.flush()  # Get the ID without committing
            
            # Create price record
            price_record = Price(
                symbol=symbol,
                ts=price_data['ts'],
                open=price_data.get('open'),
                high=price_data.get('high'),
                low=price_data.get('low'),
                close=price_data.get('close'),
                volume=price_data.get('volume'),
                created_at=price_data['created_at']
            )
            
            self.db_session.add(price_record)
            self.db_session.commit()
            
            logger.info(f"Successfully saved price data for {symbol}")
            return True
            
        except IntegrityError as e:
            self.db_session.rollback()
            logger.warning(f"Data already exists for {symbol} at {price_data['ts']}: {str(e)}")
            return False
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error saving data to database: {str(e)}")
            return False
    
    def collect_and_save(self, symbol: str) -> bool:
        """
        Convenience method to fetch and save ticker data in one call
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            bool: True if successful, False otherwise
        """
        ticker_data = self.fetch_ticker_data(symbol)
        if ticker_data:
            return self.save_to_db(ticker_data)
        return False
    
    def collect_multiple_tickers(self, symbols: list) -> Dict[str, bool]:
        """
        Collect data for multiple ticker symbols
        
        Args:
            symbols: List of ticker symbols
            
        Returns:
            Dict mapping symbol to success status
        """
        results = {}
        
        for symbol in symbols:
            logger.info(f"Processing ticker: {symbol}")
            results[symbol] = self.collect_and_save(symbol)
        
        successful_count = sum(1 for success in results.values() if success)
        logger.info(f"Collected data for {successful_count}/{len(symbols)} tickers")
        
        return results


# Utility function to test the collector
def test_collector():
    """
    Test function for the Yahoo Finance collector
    """
    from app.db.base import SessionLocal
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Initialize collector
        collector = YahooCollector(db_session=db)
        
        # Test with popular tickers
        test_symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        print("Testing Yahoo Finance Collector...")
        print("-" * 40)
        
        for symbol in test_symbols:
            print(f"Testing {symbol}...")
            data = collector.fetch_ticker_data(symbol)
            
            if data:
                print(f"✅ {symbol}: ${data['close']:.2f}")
                # Try to save to database
                if collector.save_to_db(data):
                    print(f"✅ Saved {symbol} to database")
                else:
                    print(f"❌ Failed to save {symbol} to database")
            else:
                print(f"❌ Failed to fetch data for {symbol}")
            print()
        
        print("Test completed!")
        
    finally:
        db.close()


if __name__ == "__main__":
    # Run test if executed directly
    test_collector()
