import threading
import time
import logging
import traceback

class MonitoringHealthChecker:
    """
    Health checker for monitoring thread with automatic restart capability
    """
    
    def __init__(self, monitor_instance):
        self.monitor = monitor_instance
        self.health_check_thread = None
        self.running = False
        self.restart_count = 0
        self.max_restarts = 10
        
    def start(self):
        """Start health checking"""
        if not self.running:
            self.running = True
            self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
            self.health_check_thread.start()
            logging.info("🏥 Health checker started")
    
    def stop(self):
        """Stop health checking"""
        self.running = False
        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)
    
    def _health_check_loop(self):
        """Main health check loop"""
        while self.running:
            try:
                # Check every 30 seconds
                time.sleep(30)
                
                if not self.running:
                    break
                
                # Check if monitoring thread is alive
                if self.monitor.running and self.monitor.monitor_thread:
                    if not self.monitor.monitor_thread.is_alive():
                        logging.warning("⚠️ Monitoring thread detected as dead!")
                        
                        if self.restart_count < self.max_restarts:
                            self.restart_count += 1
                            logging.info(f"🔄 Attempting restart #{self.restart_count}")
                            
                            # Restart monitoring
                            self.monitor.start_monitoring()
                            
                            # Send alert about restart
                            self.monitor._add_alert(
                                0,
                                "System Status",
                                f"🔄 Monitoring thread automatically restarted (#{self.restart_count})",
                                "system"
                            )
                        else:
                            logging.error(f"🛑 Max restarts ({self.max_restarts}) reached, stopping health checker")
                            self.running = False
                            
                            self.monitor._add_alert(
                                0,
                                "System Error",
                                f"⚠️ Monitoring failed after {self.max_restarts} restart attempts",
                                "system"
                            )
                    else:
                        # Thread is alive, reset restart count if it's been stable
                        if self.restart_count > 0:
                            logging.info("✅ Monitoring thread stable, resetting restart count")
                            self.restart_count = 0
                            
            except Exception as e:
                logging.error(f"Error in health check loop: {e}")
                logging.error(traceback.format_exc())
                time.sleep(60)  # Wait longer on error
        
        logging.info("Health checker stopped")

class ConnectionPoolManager:
    """
    Manages HTTP connection pooling for better performance and reliability
    """
    
    def __init__(self):
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        # Configure adapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=retry_strategy
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default timeout
        self.default_timeout = 10
        
    def get(self, url, **kwargs):
        """GET request with connection pooling"""
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.default_timeout
        return self.session.get(url, **kwargs)
    
    def post(self, url, **kwargs):
        """POST request with connection pooling"""
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.default_timeout
        return self.session.post(url, **kwargs)
    
    def close(self):
        """Close the session and clean up connections"""
        self.session.close()

# Global connection pool for the application
global_connection_pool = None

def get_connection_pool():
    """Get or create the global connection pool"""
    global global_connection_pool
    if global_connection_pool is None:
        global_connection_pool = ConnectionPoolManager()
    return global_connection_pool

def cleanup_connection_pool():
    """Clean up the global connection pool"""
    global global_connection_pool
    if global_connection_pool:
        global_connection_pool.close()
        global_connection_pool = None