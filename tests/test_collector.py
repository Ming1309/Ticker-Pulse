#!/usr/bin/env python3
"""
Test script for Yahoo Finance Collector
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collectors.yahoo_collector import YahooCollector
from app.db.base import SessionLocal

def main():
    """Test the Yahoo Finance collector"""
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Initialize collector
        collector = YahooCollector(db_session=db)
        
        # Test fetching data for popular tickers
        test_symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        print('Testing Yahoo Finance Collector...')
        print('=' * 50)
        
        for symbol in test_symbols:
            print(f'\nTesting {symbol}...')
            
            # Fetch data
            data = collector.fetch_ticker_data(symbol)
            
            if data:
                print(f'✅ Successfully fetched {symbol} data:')
                print(f'   Close: ${data["close"]:.2f}')
                print(f'   Volume: {data["volume"]:,}')
                print(f'   High: ${data["high"]:.2f}')
                print(f'   Low: ${data["low"]:.2f}')
                print(f'   Timestamp: {data["ts"]}')
                
                # Try to save to database
                if collector.save_to_db(data):
                    print(f'✅ Successfully saved {symbol} to database')
                else:
                    print(f'⚠️  Could not save {symbol} to database (may already exist)')
                    
            else:
                print(f'❌ Failed to fetch data for {symbol}')
        
        print('\n' + '=' * 50)
        print('Test completed!')
        
    except Exception as e:
        print(f'❌ Error during testing: {str(e)}')
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
