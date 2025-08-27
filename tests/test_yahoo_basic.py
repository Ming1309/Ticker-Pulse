"""
Simple test for Yahoo Finance data fetching
"""

import yfinance as yf
from datetime import datetime

def test_yahoo_finance():
    """Test basic Yahoo Finance functionality"""
    
    print("Testing Yahoo Finance API...")
    print("=" * 40)
    
    # Test symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    for symbol in symbols:
        try:
            print(f"\nFetching data for {symbol}...")
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Get recent data
            hist = ticker.history(period="1d", interval="1m")
            
            if not hist.empty:
                latest = hist.iloc[-1]
                print(f"✅ {symbol} - Latest Close: ${latest['Close']:.2f}")
                print(f"   Volume: {int(latest['Volume']):,}")
                print(f"   High: ${latest['High']:.2f}, Low: ${latest['Low']:.2f}")
            else:
                print(f"❌ No data available for {symbol}")
                
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {str(e)}")
    
    print("\n" + "=" * 40)
    print("Yahoo Finance test completed!")

if __name__ == "__main__":
    test_yahoo_finance()
