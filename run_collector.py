#!/usr/bin/env python3
"""
MarketPulse Standalone Collector Runner
Easy-to-use script for running the collector agent
"""

from collectors.collector_agent import get_collector_agent
import time
import signal
import sys

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print('\n🛑 Stopping collector...')
    agent = get_collector_agent()
    agent.stop_collection()
    agent.shutdown()
    print('✅ Collector stopped. Goodbye!')
    sys.exit(0)

def main():
    print('🚀 MarketPulse Collector Agent')
    print('=' * 50)
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Get collector agent
    agent = get_collector_agent()
    
    # Configuration
    DEFAULT_TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
    DEFAULT_INTERVAL = 60  # 1 minute
    
    print(f'📊 Default tickers: {", ".join(DEFAULT_TICKERS)}')
    print(f'⏰ Default interval: {DEFAULT_INTERVAL} seconds')
    print()
    
    # Ask user for custom tickers
    user_input = input('Enter tickers (comma-separated) or press Enter for default: ').strip()
    
    if user_input:
        tickers = [ticker.strip().upper() for ticker in user_input.split(',') if ticker.strip()]
    else:
        tickers = DEFAULT_TICKERS
    
    # Ask for interval
    interval_input = input(f'Enter interval in seconds (default {DEFAULT_INTERVAL}): ').strip()
    
    if interval_input.isdigit():
        interval = max(int(interval_input), 30)  # Minimum 30 seconds
    else:
        interval = DEFAULT_INTERVAL
    
    print()
    print(f'🎯 Starting collection for: {", ".join(tickers)}')
    print(f'⏰ Collection interval: {interval} seconds')
    print(f'🛑 Press Ctrl+C to stop')
    print('=' * 50)
    
    # Start collection
    if agent.start_collection(tickers, interval_seconds=interval):
        print('✅ Collection started successfully!')
        print()
        
        try:
            # Monitor and display stats
            while True:
                time.sleep(10)  # Check every 10 seconds
                status = agent.get_status()
                stats = status['stats']
                
                print(f'📊 Stats: Total={stats["total_collections"]}, '
                      f'Success={stats["successful_collections"]}, '
                      f'Failed={stats["failed_collections"]} | '
                      f'Next run: {status.get("next_run_time", "N/A")}')
                
        except KeyboardInterrupt:
            # This will be handled by signal_handler
            pass
            
    else:
        print('❌ Failed to start collection!')
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
