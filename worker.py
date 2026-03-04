#!/usr/bin/env python3
"""
MLB Alert Worker Process - Implements stability patterns from Replit playbook
"""
import asyncio
import time
import os
import sys
import logging
import traceback
from datetime import datetime
from tenacity import retry, wait_exponential, stop_after_attempt, RetryError

# Import our monitoring classes
from mlb_monitor import MLBMonitor

# Environment configuration
APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = logging.DEBUG if APP_ENV == "development" else logging.INFO

# Configure structured logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s - worker_pid=%(process)d'
)

logger = logging.getLogger(__name__)

class HealthyWorker:
    """Watchdog wrapper for the MLB monitoring loop"""
    
    def __init__(self):
        self.monitor = None
        self.start_time = datetime.utcnow()
        self.iteration_count = 0
        self.last_successful_run = datetime.utcnow()
        
    def initialize_monitor(self):
        """Initialize MLB monitor with error handling"""
        try:
            logger.info("Initializing MLB Monitor...")
            self.monitor = MLBMonitor()
            logger.info("MLB Monitor initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize monitor: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def run_monitoring_loop(self):
        """Main monitoring loop with proper error handling"""
        if not self.initialize_monitor():
            raise Exception("Failed to initialize MLB Monitor")
            
        logger.info(f"Starting MLB monitoring loop in {APP_ENV} mode...")
        
        while True:
            try:
                # Run one monitoring iteration
                await self.run_single_iteration()
                self.last_successful_run = datetime.utcnow()
                self.iteration_count += 1
                
                # Log health status every 50 iterations
                if self.iteration_count % 50 == 0:
                    uptime = (datetime.utcnow() - self.start_time).total_seconds()
                    logger.info(f"Worker healthy - iteration={self.iteration_count}, uptime={uptime:.1f}s")
                
                # Wait before next iteration
                await asyncio.sleep(0.5)
                
            except KeyboardInterrupt:
                logger.info("Received shutdown signal, stopping worker...")
                break
            except Exception as e:
                logger.error(f"Error in monitoring iteration {self.iteration_count}: {e}")
                logger.error(f"Last payload context: {getattr(self.monitor, 'last_game_data', 'none')}")
                logger.error(traceback.format_exc())
                
                # Progressive backoff: 1s -> 2s -> 5s -> 10s -> 30s -> 60s (max)
                backoff_delay = min(60, 2 ** min(5, self.iteration_count % 6))
                logger.warning(f"Backing off for {backoff_delay}s before retry...")
                await asyncio.sleep(backoff_delay)
    
    async def run_single_iteration(self):
        """Run a single monitoring iteration"""
        try:
            # Run monitoring check using existing method
            self.monitor._check_monitored_games()
            
            # Store last successful game data for debugging
            self.monitor.last_game_data = {
                'iteration': self.iteration_count,
                'timestamp': datetime.utcnow().isoformat(),
                'alerts_count': len(self.monitor.alerts) if hasattr(self.monitor, 'alerts') else 0
            }
                
        except Exception as e:
            logger.error(f"Single iteration failed: {e}")
            raise

@retry(
    wait=wait_exponential(multiplier=1, min=1, max=60),
    stop=stop_after_attempt(999999),
    reraise=True
)
def main():
    """Main entry point with retry wrapper"""
    try:
        worker = HealthyWorker()
        asyncio.run(worker.run_monitoring_loop())
    except KeyboardInterrupt:
        logger.info("Worker shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
        logger.error(traceback.format_exc())
        
        # Send crash notification if configured
        if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
            try:
                import requests
                bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
                chat_id = os.getenv("TELEGRAM_CHAT_ID")
                
                crash_msg = f"🚨 MLB Worker Crashed\n\nTime: {datetime.utcnow()}\nError: {str(e)[:200]}\nRestarting..."
                
                requests.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    data={"chat_id": chat_id, "text": crash_msg},
                    timeout=10
                )
            except:
                pass  # Don't fail on notification failure
        
        raise

if __name__ == "__main__":
    logger.info(f"Starting MLB Alert Worker (env={APP_ENV})")
    main()