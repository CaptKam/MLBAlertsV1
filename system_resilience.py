"""
System resilience utilities for MLB Monitor
Provides automatic recovery, resource management, and error handling
"""

import logging
import time
import threading
import os
import signal
import sys
from typing import Optional, Callable, Any
from datetime import datetime, timedelta

class AutoRestartManager:
    """
    Manages automatic restart of critical components
    """
    
    def __init__(self, component_name: str, start_func: Callable, check_func: Callable):
        self.component_name = component_name
        self.start_func = start_func
        self.check_func = check_func
        self.restart_count = 0
        self.max_restarts = 10
        self.restart_window = timedelta(hours=1)
        self.restart_times = []
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start monitoring the component"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logging.info(f"🔍 Auto-restart monitoring started for {self.component_name}")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def _monitor_loop(self):
        """Monitor and restart component if needed"""
        while self.monitoring:
            try:
                time.sleep(30)  # Check every 30 seconds
                
                if not self.monitoring:
                    break
                
                # Clean old restart times
                cutoff_time = datetime.now() - self.restart_window
                self.restart_times = [t for t in self.restart_times if t > cutoff_time]
                
                # Check if component is healthy
                if not self.check_func():
                    logging.warning(f"⚠️ {self.component_name} health check failed")
                    
                    # Check restart limit
                    if len(self.restart_times) >= self.max_restarts:
                        logging.error(f"🛑 {self.component_name} exceeded restart limit")
                        self.monitoring = False
                        break
                    
                    # Attempt restart
                    logging.info(f"🔄 Attempting to restart {self.component_name}")
                    try:
                        self.start_func()
                        self.restart_times.append(datetime.now())
                        self.restart_count += 1
                        logging.info(f"✅ {self.component_name} restarted successfully (count: {self.restart_count})")
                    except Exception as e:
                        logging.error(f"❌ Failed to restart {self.component_name}: {e}")
                        
            except Exception as e:
                logging.error(f"Error in auto-restart monitor for {self.component_name}: {e}")
                
        logging.info(f"Auto-restart monitoring stopped for {self.component_name}")

class ResourceManager:
    """
    Manages system resources and cleanup
    """
    
    def __init__(self):
        self.resources = []
        self.cleanup_functions = []
        self._setup_signal_handlers()
        
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logging.info(f"⚠️ Received signal {signum}, initiating graceful shutdown...")
            self.cleanup_all()
            sys.exit(0)
        
        # Handle common termination signals
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
    def register_resource(self, resource: Any, cleanup_func: Optional[Callable] = None):
        """Register a resource for cleanup"""
        self.resources.append(resource)
        if cleanup_func:
            self.cleanup_functions.append(cleanup_func)
    
    def cleanup_all(self):
        """Clean up all registered resources"""
        logging.info("🧹 Cleaning up resources...")
        
        for cleanup_func in self.cleanup_functions:
            try:
                cleanup_func()
            except Exception as e:
                logging.error(f"Error during cleanup: {e}")
        
        # Clear resources
        self.resources.clear()
        self.cleanup_functions.clear()
        
        logging.info("✅ Resource cleanup completed")

class CircuitBreaker:
    """
    Circuit breaker pattern for external service calls
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        
        # Check if circuit should be opened
        if self.state == "open":
            if (self.last_failure_time and 
                time.time() - self.last_failure_time > self.recovery_timeout):
                self.state = "half-open"
                logging.info("🔄 Circuit breaker entering half-open state")
            else:
                raise Exception("Circuit breaker is open - service unavailable")
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset if in half-open state
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
                logging.info("✅ Circuit breaker closed - service recovered")
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logging.error(f"⚡ Circuit breaker opened after {self.failure_count} failures")
            
            raise e

class RateLimiter:
    """
    Rate limiter for API calls
    """
    
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self.lock = threading.Lock()
        
    def allow_request(self) -> bool:
        """Check if request is allowed under rate limit"""
        with self.lock:
            now = time.time()
            
            # Remove old calls outside time window
            self.calls = [t for t in self.calls if now - t < self.time_window]
            
            # Check if under limit
            if len(self.calls) < self.max_calls:
                self.calls.append(now)
                return True
            
            return False
    
    def wait_if_needed(self):
        """Wait if rate limit exceeded"""
        while not self.allow_request():
            time.sleep(0.1)

# Global instances
resource_manager = ResourceManager()
mlb_api_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
api_rate_limiter = RateLimiter(max_calls=100, time_window=60)  # 100 calls per minute

def ensure_monitoring_health(monitor_instance):
    """
    Ensure monitoring thread is healthy and restart if needed
    """
    if monitor_instance.running:
        if not monitor_instance.monitor_thread or not monitor_instance.monitor_thread.is_alive():
            logging.warning("⚠️ Monitoring thread not alive, restarting...")
            monitor_instance.start_monitoring()
            return True
    return False