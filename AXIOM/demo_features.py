#!/usr/bin/env python3
"""
Demonstration script showcasing all new AXIOM features.

This script demonstrates:
1. Structured logging
2. Error handling with retry
3. Input validation
4. Health checks
5. Performance monitoring
"""

import asyncio
from pathlib import Path

# Initialize logging first
from axiom.utils.logging import setup_logging, get_logger, PerformanceLogger
from axiom.utils.errors import ErrorCode, EventBusError, PolicyError
from axiom.utils.health import HealthChecker, HealthStatus
from axiom.policy.input_validation import (
    InputSanitizationPolicyEnhanced,
    ConfigPathValidationPolicy,
    AlphanumericWithPunctuationPolicy
)
from axiom.policy.policies import PolicyContext
from axiom.bus.event_bus import EventBus
from axiom.bus.events import Event, EventType

# Setup logging with debug enabled
setup_logging(debug=True)
logger = get_logger(__name__)


def demonstrate_logging():
    """Demonstrate structured logging."""
    print("\n" + "=" * 70)
    print("1. STRUCTURED LOGGING DEMONSTRATION")
    print("=" * 70)
    
    logger.info("This is an info message", user="demo", action="testing")
    logger.warning("This is a warning", component="demo", severity="low")
    logger.error("This is an error", error_code="DEMO-001", retryable=True)
    
    # Performance logging
    with PerformanceLogger(logger, "demo_operation", component="demo"):
        import time
        time.sleep(0.1)  # Simulate work
    
    print("\n✓ Check logs/ directory for detailed JSON logs")
    print("✓ Console shows WARNING and above")
    print("✓ File contains all levels with full context")


def demonstrate_error_handling():
    """Demonstrate structured error handling."""
    print("\n" + "=" * 70)
    print("2. ERROR HANDLING DEMONSTRATION")
    print("=" * 70)
    
    # Create a structured error
    error = EventBusError(
        error_code=ErrorCode.BUS_QUEUE_FULL,
        message="Event queue is at capacity",
        details={"queue_size": 1000, "max_size": 1000},
        user_message="System is busy, please try again",
        retry_allowed=True
    )
    
    print(f"\n📋 Technical Error Info:")
    print(f"  Code: {error.error_code}")
    print(f"  Message: {error.message}")
    print(f"  Details: {error.details}")
    print(f"  Retry Allowed: {error.retry_allowed}")
    
    print(f"\n👤 User-Facing Message:")
    print(f"  {error.user_message}")
    
    print(f"\n📊 Structured Error Dict:")
    import json
    print(json.dumps(error.to_dict(), indent=2, default=str))


def demonstrate_input_validation():
    """Demonstrate input validation policies."""
    print("\n" + "=" * 70)
    print("3. INPUT VALIDATION DEMONSTRATION")
    print("=" * 70)
    
    validator = InputSanitizationPolicyEnhanced()
    
    # Test cases
    test_inputs = [
        ("Hello, world!", "Normal input"),
        ("'; DROP TABLE users;--", "SQL injection attempt"),
        ("<script>alert('xss')</script>", "XSS attempt"),
        ("../../../etc/passwd", "Path traversal attempt"),
        ("A" * 600, "Too long input"),
    ]
    
    for input_text, description in test_inputs:
        context = PolicyContext(user_input=input_text, response="")
        result = validator.evaluate(context)
        
        status = "✓ PASS" if result.passed else "✗ BLOCKED"
        print(f"\n{status}: {description}")
        print(f"  Input: {input_text[:50]}{'...' if len(input_text) > 50 else ''}")
        
        if not result.passed:
            print(f"  Violations: {list(result.violations.keys())}")


def demonstrate_health_checks():
    """Demonstrate health check system."""
    print("\n" + "=" * 70)
    print("4. HEALTH CHECK DEMONSTRATION")
    print("=" * 70)
    
    checker = HealthChecker()
    
    # Create mock event bus
    event_bus = EventBus()
    event_bus.register_publisher("demo", [EventType.CONVERSATION_TURN.value])
    
    # Run health checks
    results = checker.check_all(event_bus=event_bus)
    
    print("\n📊 System Health Report:")
    print("-" * 70)
    
    for component, result in results.items():
        status_symbol = {
            "healthy": "✓",
            "degraded": "⚠",
            "unhealthy": "✗"
        }.get(result.status.value, "?")
        
        critical = " [CRITICAL]" if result.critical else ""
        print(f"{status_symbol} {component.upper()}{critical}")
        print(f"  Status: {result.status.value}")
        print(f"  Message: {result.message}")
        
        if result.details:
            for key, value in list(result.details.items())[:3]:  # Show first 3
                print(f"    {key}: {value}")
    
    print("-" * 70)
    print(f"Overall: {'✓ HEALTHY' if checker.is_healthy() else '✗ UNHEALTHY'}")


async def demonstrate_performance_tracking():
    """Demonstrate performance tracking with event bus."""
    print("\n" + "=" * 70)
    print("5. PERFORMANCE TRACKING DEMONSTRATION")
    print("=" * 70)
    
    bus = EventBus()
    bus.register_publisher("perf_demo", [EventType.CONVERSATION_TURN.value])
    
    received_events = []
    def handler(event):
        received_events.append(event)
    
    bus.subscribe(EventType.CONVERSATION_TURN.value, handler)
    
    print("\n📊 Publishing events with performance tracking...")
    
    # Publish multiple events
    for i in range(3):
        event = Event(
            event_type=EventType.CONVERSATION_TURN.value,
            payload={"message": f"Test message {i+1}"},
            source="perf_demo"
        )
        await bus.publish(event)
    
    print(f"\n✓ Published 3 events successfully")
    print(f"✓ Check logs for detailed timing information")
    print(f"✓ Each publish operation is tracked with duration_seconds")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("AXIOM FEATURE DEMONSTRATION")
    print("All new Phase 1 capabilities")
    print("=" * 70)
    
    try:
        # 1. Logging
        demonstrate_logging()
        
        # 2. Error handling
        demonstrate_error_handling()
        
        # 3. Input validation
        demonstrate_input_validation()
        
        # 4. Health checks
        demonstrate_health_checks()
        
        # 5. Performance tracking
        asyncio.run(demonstrate_performance_tracking())
        
        print("\n" + "=" * 70)
        print("✅ DEMONSTRATION COMPLETE")
        print("=" * 70)
        print("\n📁 Check the following locations:")
        print("  • logs/axiom.log - Detailed JSON logs")
        print("  • Console output - User-friendly messages")
        print("\n🎯 All Phase 1 features are operational!")
        
    except Exception as e:
        logger.critical("Demonstration failed", error=str(e))
        raise


if __name__ == "__main__":
    main()
