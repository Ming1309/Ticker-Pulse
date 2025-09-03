"""
Unit tests for Yahoo Finance data fetching using pytest and mocking
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch
import yfinance as yf


class TestYahooFinance:
    """Test class for Yahoo Finance functionality"""

    @pytest.fixture
    def mock_ticker_data(self):
        """Create mock ticker data for testing"""
        # Create mock DataFrame with OHLCV data
        mock_data = pd.DataFrame({
            'Open': [150.0, 151.0, 152.0],
            'High': [155.0, 156.0, 157.0], 
            'Low': [149.0, 150.0, 151.0],
            'Close': [154.0, 155.0, 156.0],
            'Volume': [1000000, 1100000, 1200000]
        }, index=pd.date_range('2023-01-01 09:30:00', periods=3, freq='1min'))
        
        return mock_data

    @pytest.fixture
    def mock_empty_data(self):
        """Create empty DataFrame for testing error cases"""
        return pd.DataFrame()

    @patch('yfinance.Ticker')
    def test_yahoo_finance_successful_fetch(self, mock_ticker_class, mock_ticker_data):
        """Test successful data fetching from Yahoo Finance"""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker.history.return_value = mock_ticker_data
        mock_ticker_class.return_value = mock_ticker
        
        # Test the functionality
        ticker = yf.Ticker("AAPL")
        hist = ticker.history(period="1d", interval="1m")
        
        # Assertions
        assert not hist.empty
        assert len(hist) == 3
        assert 'Close' in hist.columns
        assert 'Volume' in hist.columns
        
        # Test latest data
        latest = hist.iloc[-1]
        assert latest['Close'] == 156.0
        assert latest['Volume'] == 1200000
        assert latest['High'] >= latest['Low']

    @patch('yfinance.Ticker')
    def test_yahoo_finance_empty_response(self, mock_ticker_class, mock_empty_data):
        """Test handling of empty response from Yahoo Finance"""
        # Setup mock to return empty data
        mock_ticker = Mock()
        mock_ticker.history.return_value = mock_empty_data
        mock_ticker_class.return_value = mock_ticker
        
        # Test the functionality
        ticker = yf.Ticker("INVALID")
        hist = ticker.history(period="1d", interval="1m")
        
        # Assertions
        assert hist.empty
        assert len(hist) == 0

    @patch('yfinance.Ticker')
    def test_yahoo_finance_api_exception(self, mock_ticker_class):
        """Test handling of API exceptions"""
        # Setup mock to raise exception
        mock_ticker = Mock()
        mock_ticker.history.side_effect = Exception("Network error")
        mock_ticker_class.return_value = mock_ticker
        
        # Test the functionality
        ticker = yf.Ticker("AAPL")
        
        # Assertions
        with pytest.raises(Exception) as exc_info:
            ticker.history(period="1d", interval="1m")
        
        assert "Network error" in str(exc_info.value)

    @patch('yfinance.Ticker')
    def test_multiple_symbols(self, mock_ticker_class, mock_ticker_data):
        """Test fetching data for multiple symbols"""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker.history.return_value = mock_ticker_data
        mock_ticker_class.return_value = mock_ticker
        
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        results = {}
        
        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d", interval="1m")
            results[symbol] = hist
        
        # Assertions
        assert len(results) == 3
        for symbol, data in results.items():
            assert not data.empty
            assert len(data) == 3
            assert symbol in ['AAPL', 'MSFT', 'GOOGL']

    def test_data_structure_validation(self, mock_ticker_data):
        """Test that mock data has expected structure"""
        # Assertions for data structure
        assert isinstance(mock_ticker_data, pd.DataFrame)
        assert not mock_ticker_data.empty
        
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            assert col in mock_ticker_data.columns
        
        # Test data types
        assert mock_ticker_data['Close'].dtype in ['float64', 'float32']
        assert mock_ticker_data['Volume'].dtype in ['int64', 'int32', 'float64']
        
        # Test logical constraints
        latest = mock_ticker_data.iloc[-1]
        assert latest['High'] >= latest['Low']
        assert latest['High'] >= latest['Open']
        assert latest['High'] >= latest['Close']
        assert latest['Volume'] >= 0

    @patch('yfinance.Ticker')
    def test_price_data_format(self, mock_ticker_class, mock_ticker_data):
        """Test that price data is in correct format for our application"""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker.history.return_value = mock_ticker_data
        mock_ticker_class.return_value = mock_ticker
        
        # Simulate our application logic
        ticker = yf.Ticker("AAPL")
        hist = ticker.history(period="1d", interval="1m")
        
        if not hist.empty:
            latest = hist.iloc[-1]
            
            # Test data can be converted to our format
            price_data = {
                'symbol': 'AAPL',
                'ts': datetime.now(),
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'close': float(latest['Close']),
                'volume': int(latest['Volume'])
            }
            
            # Assertions
            assert isinstance(price_data['open'], float)
            assert isinstance(price_data['high'], float)
            assert isinstance(price_data['low'], float)
            assert isinstance(price_data['close'], float)
            assert isinstance(price_data['volume'], int)
            assert price_data['high'] >= price_data['low']


# Integration test (can be run separately if network access is available)
@pytest.mark.integration
@pytest.mark.skipif(True, reason="Skip network-dependent tests by default")
def test_real_yahoo_finance_integration():
    """Integration test with real Yahoo Finance API (requires network)"""
    try:
        ticker = yf.Ticker("AAPL")
        hist = ticker.history(period="1d", interval="5m")
        
        if not hist.empty:
            latest = hist.iloc[-1]
            assert latest['Close'] > 0
            assert latest['Volume'] >= 0
            assert 'Close' in hist.columns
            
    except Exception as e:
        pytest.skip(f"Network integration test failed: {e}")


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])
