"""
Test Yahoo Collector with Database
"""

import sys
import os
sys.path.append('/Users/ming/Documents/Code/Ticker-Pulse')

import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import logging

# Database imports
from app.db.base import SessionLocal
from app.db.models import Ticker, Price

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YahooCollectorTest:
    """Test version of Yahoo Collector"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def fetch_ticker_data(self, symbol: str) -> Optional[Dict]:
        """Fetch latest ticker data from Yahoo Finance"""
        try:
            logger.info(f"Fetching data for ticker: {symbol}")
            
            # Create yfinance Ticker object
            ticker = yf.Ticker(symbol)
            
            # Get latest 1-day data with 1-minute intervals
            hist_data = ticker.history(period="1d", interval="5m")  # Use 5m for more reliable data
            
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
        """Save ticker price data to database"""
        try:
            symbol = price_data['symbol']
            
            # Check if ticker exists, create if not
            ticker = self.db.query(Ticker).filter(Ticker.symbol == symbol).first()
            
            if not ticker:
                logger.info(f"Creating new ticker: {symbol}")
                ticker = Ticker(
                    symbol=symbol,
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                self.db.add(ticker)
                self.db.flush()
            
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
            
            self.db.add(price_record)
            self.db.commit()
            
            logger.info(f"Successfully saved price data for {symbol}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving data to database: {str(e)}")
            return False
    
    def test_full_workflow(self):
        """Test complete workflow"""
        test_symbols = ['AAPL', 'MSFT']
        
        print("Testing Yahoo Collector with Database...")
        print("=" * 50)
        
        for symbol in test_symbols:
            print(f"\nTesting {symbol}...")
            
            # Fetch data
            data = self.fetch_ticker_data(symbol)
            
            if data:
                print(f"✅ Fetched {symbol}: ${data['close']:.2f}")
                
                # Save to database
                if self.save_to_db(data):
                    print(f"✅ Saved {symbol} to database")
                else:
                    print(f"❌ Failed to save {symbol} to database")
            else:
                print(f"❌ Failed to fetch {symbol}")
        
        print("\nTest completed!")
        
    def close(self):
        """Close database connection"""
        self.db.close()

def main():
    collector = YahooCollectorTest()
    try:
        collector.test_full_workflow()
    finally:
        collector.close()

if __name__ == "__main__":
    main()
