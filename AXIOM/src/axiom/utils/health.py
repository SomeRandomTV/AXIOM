"""
Health check system for AXIOM.

Monitors:
- Database connection/integrity
- Event bus operational status
- Policy engine loaded and ready
- Dialog manager initialized
- Disk space available
- Memory usage
- Configuration loaded correctly
"""

import psutil
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from axiom.utils.logging import get_logger, PerformanceLogger
from axiom.utils.errors import ErrorCode, SystemError

logger = get_logger(__name__)


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a single health check."""
    component: str
    status: HealthStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    critical: bool = False  # If True, failure prevents startup


class HealthChecker:
    """
    Performs comprehensive health checks on AXIOM components.
    """
    
    # Thresholds
    MIN_DISK_SPACE_GB = 1.0  # Warn below 1GB
    CRITICAL_DISK_SPACE_GB = 0.1  # Error below 100MB
    MAX_MEMORY_PERCENT = 80.0  # Warn above 80%
    CRITICAL_MEMORY_PERCENT = 95.0  # Error above 95%
    
    def __init__(self):
        self.results: Dict[str, HealthCheckResult] = {}
    
    def check_all(
        self,
        state_store=None,
        event_bus=None,
        policy_engine=None,
        dialog_manager=None,
        config=None
    ) -> Dict[str, HealthCheckResult]:
        """
        Run all health checks.
        
        Args:
            state_store: StateStore instance to check
            event_bus: EventBus instance to check
            policy_engine: PolicyEngine instance to check
            dialog_manager: DialogManager instance to check
            config: Configuration instance to check
        
        Returns:
            Dictionary of health check results by component
        """
        with PerformanceLogger(logger, "health_check"):
            self.results = {}
            
            # Critical components (startup blockers)
            if config is not None:
                self.check_configuration(config)
            
            if state_store is not None:
                self.check_database(state_store)
            
            # Non-critical components
            if event_bus is not None:
                self.check_event_bus(event_bus)
            
            if policy_engine is not None:
                self.check_policy_engine(policy_engine)
            
            if dialog_manager is not None:
                self.check_dialog_manager(dialog_manager)
            
            # System resources
            self.check_disk_space()
            self.check_memory_usage()
            
            logger.info(
                "Health check completed",
                total_checks=len(self.results),
                healthy=sum(1 for r in self.results.values() if r.status == HealthStatus.HEALTHY),
                degraded=sum(1 for r in self.results.values() if r.status == HealthStatus.DEGRADED),
                unhealthy=sum(1 for r in self.results.values() if r.status == HealthStatus.UNHEALTHY)
            )
            
            return self.results
    
    def check_database(self, state_store) -> HealthCheckResult:
        """Check database connection and integrity."""
        try:
            # Check if database file exists
            if not state_store.db_path.exists():
                result = HealthCheckResult(
                    component="database",
                    status=HealthStatus.UNHEALTHY,
                    message="Database file does not exist",
                    details={"path": str(state_store.db_path)},
                    critical=True
                )
            else:
                # Try a simple query
                with state_store._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM conversation_turns")
                    count = cursor.fetchone()[0]
                
                result = HealthCheckResult(
                    component="database",
                    status=HealthStatus.HEALTHY,
                    message="Database connection successful",
                    details={
                        "path": str(state_store.db_path),
                        "conversation_turns": count
                    },
                    critical=True
                )
            
            logger.info(
                "Database health check",
                status=result.status.value,
                details=result.details
            )
        
        except Exception as e:
            result = HealthCheckResult(
                component="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database check failed: {str(e)}",
                details={"error": str(e)},
                critical=True
            )
            logger.error(
                "Database health check failed",
                error=str(e)
            )
        
        self.results["database"] = result
        return result
    
    def check_event_bus(self, event_bus) -> HealthCheckResult:
        """Check event bus operational status."""
        try:
            publisher_count = len(event_bus._publishers)
            subscriber_count = sum(len(subs) for subs in event_bus._subscribers.values())
            queue_size = event_bus._event_queue.qsize()
            
            status = HealthStatus.HEALTHY
            message = "Event bus operational"
            
            # Check for potential issues
            if queue_size > event_bus._event_queue.maxsize * 0.8:
                status = HealthStatus.DEGRADED
                message = "Event queue near capacity"
            
            result = HealthCheckResult(
                component="event_bus",
                status=status,
                message=message,
                details={
                    "publishers": publisher_count,
                    "subscribers": subscriber_count,
                    "queue_size": queue_size,
                    "queue_max": event_bus._event_queue.maxsize
                },
                critical=False
            )
            
            logger.info(
                "Event bus health check",
                status=result.status.value,
                details=result.details
            )
        
        except Exception as e:
            result = HealthCheckResult(
                component="event_bus",
                status=HealthStatus.UNHEALTHY,
                message=f"Event bus check failed: {str(e)}",
                details={"error": str(e)},
                critical=False
            )
            logger.error(
                "Event bus health check failed",
                error=str(e)
            )
        
        self.results["event_bus"] = result
        return result
    
    def check_policy_engine(self, policy_engine) -> HealthCheckResult:
        """Check policy engine loaded and ready."""
        try:
            policy_count = len(policy_engine._policies)
            
            if policy_count == 0:
                status = HealthStatus.DEGRADED
                message = "No policies loaded"
            else:
                status = HealthStatus.HEALTHY
                message = f"{policy_count} policies loaded"
            
            result = HealthCheckResult(
                component="policy_engine",
                status=status,
                message=message,
                details={"policy_count": policy_count},
                critical=False
            )
            
            logger.info(
                "Policy engine health check",
                status=result.status.value,
                details=result.details
            )
        
        except Exception as e:
            result = HealthCheckResult(
                component="policy_engine",
                status=HealthStatus.UNHEALTHY,
                message=f"Policy engine check failed: {str(e)}",
                details={"error": str(e)},
                critical=False
            )
            logger.error(
                "Policy engine health check failed",
                error=str(e)
            )
        
        self.results["policy_engine"] = result
        return result
    
    def check_dialog_manager(self, dialog_manager) -> HealthCheckResult:
        """Check dialog manager initialized."""
        try:
            # Check if components are initialized
            has_intent_detector = dialog_manager.intent_detector is not None
            has_response_generator = dialog_manager.response_generator is not None
            
            if has_intent_detector and has_response_generator:
                status = HealthStatus.HEALTHY
                message = "Dialog manager fully initialized"
            else:
                status = HealthStatus.DEGRADED
                message = "Dialog manager partially initialized"
            
            result = HealthCheckResult(
                component="dialog_manager",
                status=status,
                message=message,
                details={
                    "intent_detector": has_intent_detector,
                    "response_generator": has_response_generator
                },
                critical=False
            )
            
            logger.info(
                "Dialog manager health check",
                status=result.status.value,
                details=result.details
            )
        
        except Exception as e:
            result = HealthCheckResult(
                component="dialog_manager",
                status=HealthStatus.UNHEALTHY,
                message=f"Dialog manager check failed: {str(e)}",
                details={"error": str(e)},
                critical=False
            )
            logger.error(
                "Dialog manager health check failed",
                error=str(e)
            )
        
        self.results["dialog_manager"] = result
        return result
    
    def check_configuration(self, config) -> HealthCheckResult:
        """Check configuration loaded correctly."""
        try:
            # Verify critical config sections exist
            has_system = hasattr(config, 'system')
            has_database = hasattr(config, 'database')
            has_va = hasattr(config, 'virtual_assistant')
            has_policy = hasattr(config, 'policy')
            
            if all([has_system, has_database, has_va, has_policy]):
                status = HealthStatus.HEALTHY
                message = "Configuration loaded successfully"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Configuration incomplete"
            
            result = HealthCheckResult(
                component="configuration",
                status=status,
                message=message,
                details={
                    "system": has_system,
                    "database": has_database,
                    "virtual_assistant": has_va,
                    "policy": has_policy
                },
                critical=True
            )
            
            logger.info(
                "Configuration health check",
                status=result.status.value,
                details=result.details
            )
        
        except Exception as e:
            result = HealthCheckResult(
                component="configuration",
                status=HealthStatus.UNHEALTHY,
                message=f"Configuration check failed: {str(e)}",
                details={"error": str(e)},
                critical=True
            )
            logger.error(
                "Configuration health check failed",
                error=str(e)
            )
        
        self.results["configuration"] = result
        return result
    
    def check_disk_space(self) -> HealthCheckResult:
        """Check available disk space."""
        try:
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024 ** 3)
            
            if free_gb < self.CRITICAL_DISK_SPACE_GB:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: Only {free_gb:.2f}GB free disk space"
            elif free_gb < self.MIN_DISK_SPACE_GB:
                status = HealthStatus.DEGRADED
                message = f"Warning: Only {free_gb:.2f}GB free disk space"
            else:
                status = HealthStatus.HEALTHY
                message = f"{free_gb:.2f}GB free disk space"
            
            result = HealthCheckResult(
                component="disk_space",
                status=status,
                message=message,
                details={
                    "free_gb": round(free_gb, 2),
                    "total_gb": round(disk.total / (1024 ** 3), 2),
                    "percent_used": disk.percent
                },
                critical=False
            )
            
            logger.info(
                "Disk space health check",
                status=result.status.value,
                details=result.details
            )
        
        except Exception as e:
            result = HealthCheckResult(
                component="disk_space",
                status=HealthStatus.UNHEALTHY,
                message=f"Disk space check failed: {str(e)}",
                details={"error": str(e)},
                critical=False
            )
            logger.error(
                "Disk space health check failed",
                error=str(e)
            )
        
        self.results["disk_space"] = result
        return result
    
    def check_memory_usage(self) -> HealthCheckResult:
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            percent_used = memory.percent
            
            if percent_used > self.CRITICAL_MEMORY_PERCENT:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: {percent_used:.1f}% memory usage"
            elif percent_used > self.MAX_MEMORY_PERCENT:
                status = HealthStatus.DEGRADED
                message = f"Warning: {percent_used:.1f}% memory usage"
            else:
                status = HealthStatus.HEALTHY
                message = f"{percent_used:.1f}% memory usage"
            
            result = HealthCheckResult(
                component="memory",
                status=status,
                message=message,
                details={
                    "percent_used": round(percent_used, 1),
                    "available_gb": round(memory.available / (1024 ** 3), 2),
                    "total_gb": round(memory.total / (1024 ** 3), 2)
                },
                critical=False
            )
            
            logger.info(
                "Memory health check",
                status=result.status.value,
                details=result.details
            )
        
        except Exception as e:
            result = HealthCheckResult(
                component="memory",
                status=HealthStatus.UNHEALTHY,
                message=f"Memory check failed: {str(e)}",
                details={"error": str(e)},
                critical=False
            )
            logger.error(
                "Memory health check failed",
                error=str(e)
            )
        
        self.results["memory"] = result
        return result
    
    def is_healthy(self) -> bool:
        """Check if all critical components are healthy."""
        critical_components = [r for r in self.results.values() if r.critical]
        return all(r.status == HealthStatus.HEALTHY for r in critical_components)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of health check results."""
        return {
            "overall_status": "healthy" if self.is_healthy() else "unhealthy",
            "components": {
                name: {
                    "status": result.status.value,
                    "message": result.message,
                    "critical": result.critical,
                    "details": result.details
                }
                for name, result in self.results.items()
            }
        }
