#!/usr/bin/env python3
"""
Production Monitoring and Logging System for MOP Gear Metrology
Comprehensive logging, metrics, and health monitoring
"""

import os
import sys
import time
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import psutil

@dataclass
class CalculationMetrics:
    """Metrics for gear calculations"""
    
    calculation_type: str  # 'spur_external', 'helical_external', etc.
    execution_time: float
    success: bool
    error_type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

@dataclass  
class SystemMetrics:
    """System performance metrics"""
    
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    active_connections: int
    requests_per_minute: float
    error_rate: float
    timestamp: str
    
    def __post_init__(self):
        if not hasattr(self, 'timestamp') or self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

class MetricsCollector:
    """Collect and aggregate performance metrics"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.calculation_history = deque(maxlen=max_history)
        self.system_history = deque(maxlen=max_history)
        self.request_times = deque(maxlen=max_history)
        self.error_counts = defaultdict(int)
        self.start_time = time.time()
        self.total_requests = 0
        self.total_errors = 0
        self._lock = threading.Lock()
    
    def record_calculation(self, metrics: CalculationMetrics):
        """Record calculation metrics"""
        with self._lock:
            self.calculation_history.append(metrics)
            self.total_requests += 1
            if not metrics.success:
                self.total_errors += 1
                self.error_counts[metrics.error_type or 'unknown'] += 1
    
    def record_request_time(self, execution_time: float):
        """Record request execution time"""
        with self._lock:
            self.request_times.append((time.time(), execution_time))
    
    def get_current_system_metrics(self) -> SystemMetrics:
        """Get current system performance metrics"""
        
        # Get system stats
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Calculate requests per minute
        current_time = time.time()
        recent_requests = [
            req_time for req_time, _ in self.request_times
            if current_time - req_time < 60
        ]
        requests_per_minute = len(recent_requests)
        
        # Calculate error rate
        recent_calculations = [
            calc for calc in self.calculation_history
            if current_time - time.mktime(time.strptime(calc.timestamp[:19], '%Y-%m-%dT%H:%M:%S')) < 300  # Last 5 minutes
        ]
        
        if recent_calculations:
            error_rate = sum(1 for calc in recent_calculations if not calc.success) / len(recent_calculations)
        else:
            error_rate = 0.0
        
        metrics = SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_mb=memory.used / (1024 * 1024),
            active_connections=0,  # Would need web server integration
            requests_per_minute=requests_per_minute,
            error_rate=error_rate,
            timestamp=datetime.utcnow().isoformat()
        )
        
        with self._lock:
            self.system_history.append(metrics)
        
        return metrics
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics"""
        
        with self._lock:
            if not self.calculation_history:
                return {
                    "status": "no_data",
                    "message": "No calculations recorded yet"
                }
            
            # Calculate statistics
            total_calcs = len(self.calculation_history)
            successful_calcs = sum(1 for calc in self.calculation_history if calc.success)
            
            execution_times = [calc.execution_time for calc in self.calculation_history if calc.success]
            
            if execution_times:
                avg_time = sum(execution_times) / len(execution_times)
                min_time = min(execution_times)
                max_time = max(execution_times)
            else:
                avg_time = min_time = max_time = 0.0
            
            # Calculate uptime
            uptime_seconds = time.time() - self.start_time
            uptime_hours = uptime_seconds / 3600
            
            return {
                "uptime_hours": round(uptime_hours, 2),
                "total_requests": self.total_requests,
                "total_calculations": total_calcs,
                "successful_calculations": successful_calcs,
                "success_rate": successful_calcs / total_calcs if total_calcs > 0 else 0.0,
                "total_errors": self.total_errors,
                "error_breakdown": dict(self.error_counts),
                "performance": {
                    "avg_execution_time": round(avg_time, 6),
                    "min_execution_time": round(min_time, 6),
                    "max_execution_time": round(max_time, 6),
                },
                "calculation_types": self._get_calculation_type_breakdown()
            }
    
    def _get_calculation_type_breakdown(self) -> Dict[str, int]:
        """Get breakdown of calculation types"""
        breakdown = defaultdict(int)
        for calc in self.calculation_history:
            breakdown[calc.calculation_type] += 1
        return dict(breakdown)

class ProductionLogger:
    """Production-grade logging system"""
    
    def __init__(self, log_level: str = "INFO", log_dir: str = "logs"):
        self.log_dir = log_dir
        self.ensure_log_directory()
        
        # Create formatters
        self.detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        self.json_formatter = self._create_json_formatter()
        
        # Set up loggers
        self.main_logger = self._setup_logger('mop.main', log_level)
        self.calculation_logger = self._setup_logger('mop.calculations', log_level)
        self.security_logger = self._setup_logger('mop.security', log_level)
        self.performance_logger = self._setup_logger('mop.performance', log_level)
        self.error_logger = self._setup_logger('mop.errors', 'WARNING')
    
    def ensure_log_directory(self):
        """Ensure log directory exists"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def _setup_logger(self, name: str, level: str) -> logging.Logger:
        """Set up individual logger"""
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # File handler
        log_file = os.path.join(self.log_dir, f"{name.split('.')[-1]}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(self.detailed_formatter)
        logger.addHandler(file_handler)
        
        # JSON file handler for structured logs
        json_file = os.path.join(self.log_dir, f"{name.split('.')[-1]}.json")
        json_handler = logging.FileHandler(json_file)
        json_handler.setFormatter(self.json_formatter)
        logger.addHandler(json_handler)
        
        # Console handler for development
        if os.getenv('MOP_DEV_MODE', 'false').lower() == 'true':
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(self.detailed_formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def _create_json_formatter(self):
        """Create JSON formatter for structured logging"""
        
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'level': record.levelname,
                    'logger': record.name,
                    'function': record.funcName,
                    'line': record.lineno,
                    'message': record.getMessage(),
                }
                
                # Add exception info if present
                if record.exc_info:
                    log_entry['exception'] = self.formatException(record.exc_info)
                
                # Add extra fields
                for key, value in record.__dict__.items():
                    if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                                 'filename', 'module', 'lineno', 'funcName', 'created', 
                                 'msecs', 'relativeCreated', 'thread', 'threadName', 
                                 'processName', 'process', 'exc_info', 'exc_text', 'stack_info']:
                        log_entry[key] = value
                
                return json.dumps(log_entry)
        
        return JSONFormatter()
    
    def log_calculation(self, calc_type: str, parameters: Dict[str, Any], 
                       execution_time: float, success: bool, error: str = None):
        """Log calculation details"""
        
        extra = {
            'calculation_type': calc_type,
            'execution_time': execution_time,
            'success': success,
            'parameters': parameters
        }
        
        if success:
            self.calculation_logger.info(
                f"Calculation completed: {calc_type} in {execution_time:.6f}s",
                extra=extra
            )
        else:
            extra['error'] = error
            self.calculation_logger.error(
                f"Calculation failed: {calc_type} - {error}",
                extra=extra
            )
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security events"""
        
        extra = {
            'event_type': event_type,
            'details': details
        }
        
        self.security_logger.warning(
            f"Security event: {event_type}",
            extra=extra
        )
    
    def log_performance_warning(self, metric: str, value: float, threshold: float):
        """Log performance warnings"""
        
        extra = {
            'metric': metric,
            'value': value,
            'threshold': threshold
        }
        
        self.performance_logger.warning(
            f"Performance warning: {metric} = {value} exceeds threshold {threshold}",
            extra=extra
        )
    
    def log_error(self, error_type: str, error_msg: str, context: Dict[str, Any] = None):
        """Log errors with context"""
        
        extra = {
            'error_type': error_type,
            'context': context or {}
        }
        
        self.error_logger.error(error_msg, extra=extra)

class HealthMonitor:
    """Monitor system health and alert on issues"""
    
    def __init__(self, metrics_collector: MetricsCollector, logger: ProductionLogger):
        self.metrics = metrics_collector
        self.logger = logger
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'error_rate': 0.05,  # 5%
            'response_time': 1.0,  # 1 second
        }
        self.alert_cooldown = 300  # 5 minutes
        self.last_alerts = {}
    
    def check_health(self) -> Dict[str, Any]:
        """Check system health and return status"""
        
        current_time = time.time()
        system_metrics = self.metrics.get_current_system_metrics()
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "alerts": []
        }
        
        # Check CPU usage
        if system_metrics.cpu_percent > self.thresholds['cpu_percent']:
            health_status["status"] = "warning"
            health_status["checks"]["cpu"] = "high"
            self._maybe_alert("high_cpu", system_metrics.cpu_percent, current_time)
        else:
            health_status["checks"]["cpu"] = "ok"
        
        # Check memory usage
        if system_metrics.memory_percent > self.thresholds['memory_percent']:
            health_status["status"] = "warning"
            health_status["checks"]["memory"] = "high"
            self._maybe_alert("high_memory", system_metrics.memory_percent, current_time)
        else:
            health_status["checks"]["memory"] = "ok"
        
        # Check error rate
        if system_metrics.error_rate > self.thresholds['error_rate']:
            health_status["status"] = "warning"
            health_status["checks"]["error_rate"] = "high"
            self._maybe_alert("high_error_rate", system_metrics.error_rate, current_time)
        else:
            health_status["checks"]["error_rate"] = "ok"
        
        # Check response time
        recent_times = [
            exec_time for req_time, exec_time in self.metrics.request_times
            if current_time - req_time < 60
        ]
        
        if recent_times:
            avg_response_time = sum(recent_times) / len(recent_times)
            if avg_response_time > self.thresholds['response_time']:
                health_status["status"] = "warning"
                health_status["checks"]["response_time"] = "slow"
                self._maybe_alert("slow_response", avg_response_time, current_time)
            else:
                health_status["checks"]["response_time"] = "ok"
        else:
            health_status["checks"]["response_time"] = "no_data"
        
        return health_status
    
    def _maybe_alert(self, alert_type: str, value: float, current_time: float):
        """Send alert if not in cooldown period"""
        
        last_alert_time = self.last_alerts.get(alert_type, 0)
        
        if current_time - last_alert_time > self.alert_cooldown:
            self.logger.log_performance_warning(
                alert_type, value, self.thresholds.get(alert_type.split('_')[-1], 0)
            )
            self.last_alerts[alert_type] = current_time

class ProductionManager:
    """Main production management class"""
    
    def __init__(self, log_level: str = "INFO", log_dir: str = "logs"):
        self.metrics = MetricsCollector()
        self.logger = ProductionLogger(log_level, log_dir)
        self.health = HealthMonitor(self.metrics, self.logger)
        self.start_time = time.time()
        
        # Start background monitoring thread
        self.monitoring_thread = threading.Thread(target=self._background_monitoring, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.main_logger.info("Production manager initialized")
    
    def _background_monitoring(self):
        """Background thread for continuous monitoring"""
        
        while True:
            try:
                # Update system metrics every 30 seconds
                self.metrics.get_current_system_metrics()
                time.sleep(30)
                
            except Exception as e:
                self.logger.log_error("monitoring_error", str(e))
                time.sleep(60)  # Wait longer on error
    
    def record_calculation(self, calc_type: str, parameters: Dict[str, Any],
                          execution_time: float, success: bool, error: str = None):
        """Record calculation with full monitoring"""
        
        # Record metrics
        metrics = CalculationMetrics(
            calculation_type=calc_type,
            execution_time=execution_time,
            success=success,
            error_type=error,
            parameters=parameters
        )
        
        self.metrics.record_calculation(metrics)
        self.metrics.record_request_time(execution_time)
        
        # Log calculation
        self.logger.log_calculation(calc_type, parameters, execution_time, success, error)
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report"""
        
        return {
            "health": self.health.check_health(),
            "metrics": self.metrics.get_summary_statistics(),
            "system": asdict(self.metrics.get_current_system_metrics())
        }

# Global production manager instance
production_manager = None

def initialize_production_monitoring(log_level: str = "INFO", log_dir: str = "logs"):
    """Initialize global production monitoring"""
    
    global production_manager
    production_manager = ProductionManager(log_level, log_dir)
    return production_manager

def get_production_manager() -> Optional[ProductionManager]:
    """Get current production manager instance"""
    return production_manager

# Example usage
if __name__ == '__main__':
    # Initialize monitoring
    pm = initialize_production_monitoring(log_level="INFO", log_dir="logs")
    
    print("Production monitoring initialized")
    print("Testing metrics collection...")
    
    # Simulate some calculations
    import random
    
    for i in range(10):
        calc_type = random.choice(['spur_external', 'helical_external', 'spur_internal'])
        execution_time = random.uniform(0.001, 0.1)
        success = random.random() > 0.1  # 90% success rate
        error = None if success else "validation_error"
        
        parameters = {
            "z": random.randint(12, 100),
            "dp": random.uniform(2, 20),
            "pa": random.choice([14.5, 20.0, 25.0])
        }
        
        pm.record_calculation(calc_type, parameters, execution_time, success, error)
        time.sleep(0.1)
    
    # Get status report
    status = pm.get_status_report()
    print("\nStatus Report:")
    print(json.dumps(status, indent=2))
    
    print("\nMonitoring system is running...")
    print("Check logs/ directory for detailed logs")