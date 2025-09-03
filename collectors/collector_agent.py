"""
MarketPulse Collector Agent
Background service for scheduled ticker data collection using APScheduler
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
import time
import threading

# Import our Yahoo Collector
import sys
import os
# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from collectors.yahoo_collector import YahooCollector
from app.db.base import SessionLocal

# Use logger from main app configuration
logger = logging.getLogger(__name__)


class CollectorAgent:
    """
    Background collector agent that manages scheduled data collection
    from multiple ticker symbols using APScheduler
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one agent instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CollectorAgent, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the collector agent"""
        if hasattr(self, '_initialized'):
            return
            
        self.scheduler = BackgroundScheduler(
            executors={'default': ThreadPoolExecutor(20)},
            job_defaults={'coalesce': False, 'max_instances': 3}
        )
        self.active_tickers = []
        self.is_running = False
        self.job_id = 'ticker_collection_job'
        self.collection_interval = 60  # Default: 1 minute
        self.stats = {
            'total_collections': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'start_time': None,
            'last_collection_time': None
        }
        
        logger.info("CollectorAgent initialized (Singleton)")
        self._initialized = True
    
    def start_collection(self, tickers: List[str], interval_seconds: int = 60) -> bool:
        """
        Start background collection for specified tickers
        
        Args:
            tickers: List of ticker symbols to collect
            interval_seconds: Collection interval in seconds (default: 60)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.is_running:
                logger.warning("Collection is already running. Stop first before starting new collection.")
                return False
            
            if not tickers:
                logger.error("No tickers provided for collection")
                return False
            
            # Validate and clean ticker symbols
            self.active_tickers = [ticker.upper().strip() for ticker in tickers if ticker.strip()]
            self.collection_interval = max(interval_seconds, 30)  # Minimum 30 seconds
            
            # Start the scheduler if not already started
            if not self.scheduler.running:
                self.scheduler.start()
                logger.info("APScheduler started")
            
            # Add the collection job
            self.scheduler.add_job(
                func=self._collect_data_job,
                trigger=IntervalTrigger(seconds=self.collection_interval),
                id=self.job_id,
                name=f"Ticker Collection Job ({', '.join(self.active_tickers)})",
                replace_existing=True
            )
            
            self.is_running = True
            self.stats['start_time'] = datetime.now()
            self.stats['total_collections'] = 0
            self.stats['successful_collections'] = 0
            self.stats['failed_collections'] = 0
            
            logger.info(f"✅ Started collection for {len(self.active_tickers)} tickers: {', '.join(self.active_tickers)}")
            logger.info(f"📊 Collection interval: {self.collection_interval} seconds")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error starting collection: {str(e)}")
            return False
    
    def stop_collection(self) -> bool:
        """
        Stop background collection
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.is_running:
                logger.warning("Collection is not currently running")
                return False
            
            # Remove the job if it exists
            if self.scheduler.get_job(self.job_id):
                self.scheduler.remove_job(self.job_id)
                logger.info(f"🛑 Removed collection job: {self.job_id}")
            
            self.is_running = False
            end_time = datetime.now()
            
            if self.stats['start_time']:
                duration = end_time - self.stats['start_time']
                logger.info(f"📊 Collection stopped. Duration: {duration}")
                logger.info(f"📈 Stats - Total: {self.stats['total_collections']}, "
                          f"Success: {self.stats['successful_collections']}, "
                          f"Failed: {self.stats['failed_collections']}")
            
            logger.info("✅ Collection stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error stopping collection: {str(e)}")
            return False
    
    def _collect_data_job(self) -> None:
        """
        Internal job function that runs on schedule
        This is called by APScheduler at specified intervals
        """
        try:
            start_time = time.time()
            logger.info(f"🔄 Starting collection cycle for {len(self.active_tickers)} tickers...")
            
            # Create new database session for this job
            db_session = SessionLocal()
            collector = YahooCollector(db_session=db_session)
            
            # Track results for this cycle
            cycle_results = {}
            successful_count = 0
            
            try:
                # Collect data for each ticker
                for ticker in self.active_tickers:
                    try:
                        logger.info(f"📈 Collecting data for {ticker}...")
                        success = collector.collect_and_save(ticker)
                        cycle_results[ticker] = success
                        
                        if success:
                            successful_count += 1
                            logger.info(f"✅ {ticker} - Success")
                        else:
                            logger.warning(f"⚠️ {ticker} - Failed")
                            
                    except Exception as ticker_error:
                        logger.error(f"❌ Error collecting {ticker}: {str(ticker_error)}")
                        cycle_results[ticker] = False
                
                # Update statistics
                self.stats['total_collections'] += 1
                self.stats['successful_collections'] += successful_count
                self.stats['failed_collections'] += (len(self.active_tickers) - successful_count)
                self.stats['last_collection_time'] = datetime.now()
                
                # Log cycle summary
                duration = time.time() - start_time
                logger.info(f"📊 Collection cycle completed in {duration:.2f}s. "
                          f"Success: {successful_count}/{len(self.active_tickers)} tickers")
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"❌ Critical error in collection job: {str(e)}")
            # Don't stop the scheduler on errors, just log and continue
    
    def get_status(self) -> Dict:
        """
        Get current collector agent status
        
        Returns:
            Dict containing status information
        """
        status = {
            'is_running': self.is_running,
            'active_tickers': self.active_tickers.copy(),
            'collection_interval': self.collection_interval,
            'scheduler_running': self.scheduler.running if self.scheduler else False,
            'stats': self.stats.copy()
        }
        
        # Add job information if running
        if self.is_running and self.scheduler:
            job = self.scheduler.get_job(self.job_id)
            if job:
                status['next_run_time'] = str(job.next_run_time) if job.next_run_time else None
                status['job_name'] = job.name
        
        return status
    
    def update_tickers(self, new_tickers: List[str]) -> bool:
        """
        Update the list of tickers being collected without stopping/starting
        
        Args:
            new_tickers: New list of ticker symbols
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.is_running:
                logger.warning("Collection is not running. Use start_collection() instead.")
                return False
            
            # Validate new tickers
            validated_tickers = [ticker.upper().strip() for ticker in new_tickers if ticker.strip()]
            
            if not validated_tickers:
                logger.error("No valid tickers provided")
                return False
            
            old_tickers = self.active_tickers.copy()
            self.active_tickers = validated_tickers
            
            # Update job name
            job = self.scheduler.get_job(self.job_id)
            if job:
                job.name = f"Ticker Collection Job ({', '.join(self.active_tickers)})"
            
            logger.info(f"🔄 Updated tickers from {old_tickers} to {self.active_tickers}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating tickers: {str(e)}")
            return False
    
    def force_collection(self) -> Dict[str, bool]:
        """
        Force an immediate collection cycle (useful for testing)
        
        Returns:
            Dict mapping ticker to success status
        """
        try:
            if not self.active_tickers:
                logger.warning("No active tickers to collect")
                return {}
            
            logger.info("🚀 Force collecting data for all active tickers...")
            
            # Create database session
            db_session = SessionLocal()
            collector = YahooCollector(db_session=db_session)
            
            try:
                results = collector.collect_multiple_tickers(self.active_tickers)
                logger.info(f"🎯 Force collection completed: {results}")
                return results
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"❌ Error in force collection: {str(e)}")
            return {}
    
    def shutdown(self) -> bool:
        """
        Shutdown the collector agent completely
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("🔄 Shutting down CollectorAgent...")
            
            # Stop collection if running
            if self.is_running:
                self.stop_collection()
            
            # Shutdown scheduler
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                logger.info("📤 APScheduler shutdown completed")
            
            # Reset instance for potential restart
            CollectorAgent._instance = None
            
            logger.info("✅ CollectorAgent shutdown completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {str(e)}")
            return False


# Global instance getter
def get_collector_agent() -> CollectorAgent:
    """
    Get the singleton CollectorAgent instance
    
    Returns:
        CollectorAgent: The singleton instance
    """
    return CollectorAgent()


# Test functions
def test_collector_agent():
    """
    Test function for the collector agent
    """
    print("Testing CollectorAgent...")
    print("=" * 50)
    
    # Get agent instance
    agent = get_collector_agent()
    
    # Test status when not running
    status = agent.get_status()
    print(f"Initial status: {status}")
    
    # Test starting collection
    test_tickers = ['AAPL', 'MSFT']
    print(f"\n🚀 Starting collection for: {test_tickers}")
    
    if agent.start_collection(test_tickers, interval_seconds=30):
        print("✅ Collection started successfully")
        
        # Show status
        status = agent.get_status()
        print(f"Running status: {status}")
        
        # Force a collection cycle
        print(f"\n🎯 Force collecting data...")
        results = agent.force_collection()
        print(f"Force collection results: {results}")
        
        # Wait a bit
        print(f"\n⏳ Waiting 5 seconds to observe scheduled collection...")
        time.sleep(5)
        
        # Show updated status
        status = agent.get_status()
        print(f"Status after wait: {status}")
        
        # Stop collection
        print(f"\n🛑 Stopping collection...")
        if agent.stop_collection():
            print("✅ Collection stopped successfully")
        else:
            print("❌ Failed to stop collection")
    else:
        print("❌ Failed to start collection")
    
    # Final status
    final_status = agent.get_status()
    print(f"\nFinal status: {final_status}")
    
    print("\n✅ Test completed!")


if __name__ == "__main__":
    # Run test if executed directly
    test_collector_agent()
