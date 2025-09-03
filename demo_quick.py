#!/usr/bin/env python3
"""
Quick Demo - MarketPulse with short interval
"""

from collectors.collector_agent import get_collector_agent
import time
import signal
import sys

def signal_handler(signum, frame):
    print('\n🛑 Demo stopped!')
    agent = get_collector_agent()
    agent.stop_collection()
    agent.shutdown()
    sys.exit(0)

print('🔥 MarketPulse Quick Demo (20-second interval)')
print('=' * 60)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

# Get agent
agent = get_collector_agent()

# Demo tickers
demo_tickers = ['AAPL', 'MSFT']
demo_interval = 20

print(f'🎯 Demo tickers: {", ".join(demo_tickers)}')
print(f'⏰ Demo interval: {demo_interval} seconds')
print(f'🛑 Press Ctrl+C to stop')
print('=' * 60)

# Start collection
if agent.start_collection(demo_tickers, interval_seconds=demo_interval):
    print('✅ Demo collection started!')
    print()
    
    try:
        # Run for 90 seconds to see multiple cycles
        start_time = time.time()
        while time.time() - start_time < 90:
            time.sleep(5)
            status = agent.get_status()
            stats = status['stats']
            
            elapsed = int(time.time() - start_time)
            print(f'[{elapsed:02d}s] 📊 Total={stats["total_collections"]}, '
                  f'Success={stats["successful_collections"]}, '
                  f'Failed={stats["failed_collections"]}')
        
        print('\n🎉 Demo completed! Stopping...')
        
    except KeyboardInterrupt:
        pass
        
    # Stop collection
    agent.stop_collection()
    agent.shutdown()
    
    # Show final results
    print('\n📊 Final Demo Results:')
    print('-' * 40)
    status = agent.get_status()
    stats = status['stats']
    print(f'Total Collections: {stats["total_collections"]}')
    print(f'Successful: {stats["successful_collections"]}')
    print(f'Failed: {stats["failed_collections"]}')
    
    # Check database
    from app.db.base import SessionLocal
    from app.db.models import Price
    from sqlalchemy import desc
    
    db = SessionLocal()
    try:
        latest_prices = db.query(Price).order_by(desc(Price.created_at)).limit(5).all()
        print(f'\n💾 Latest 5 price records:')
        for price in latest_prices:
            close_price = price.close if price.close is not None else 0.0
            print(f'  {price.symbol}: ${close_price:.2f} at {price.created_at}')
    finally:
        db.close()
        
else:
    print('❌ Failed to start demo!')

print('\n✅ Demo finished!')
