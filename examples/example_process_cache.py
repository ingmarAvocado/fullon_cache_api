#!/usr/bin/env python3
"""
Process Cache WebSocket Operations Example

PROTOTYPE - Shows desired WebSocket API pattern. 
Will be updated to use real WebSocket server like fullon_cache examples.

Usage:
    python example_process_cache.py --operations basic --verbose
    python example_process_cache.py --operations monitoring --duration 30
"""

import argparse
import asyncio
import random
import sys
import time
from typing import AsyncIterator, Dict, Any, List


class MockProcessWebSocketAPI:
    """MOCK - will be replaced with real WebSocket client."""
    
    def __init__(self, ws_url: str = "ws://localhost:8000"):
        self.ws_url = ws_url

    async def __aenter__(self):
        print("🔌 Process WebSocket connected (MOCK)")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("🔌 Process WebSocket disconnected (MOCK)")

    # READ-ONLY Process Operations
    async def get_active_processes(self, process_type: str = None, 
                                 component: str = None, since_minutes: int = 5) -> List[Dict[str, Any]]:
        await asyncio.sleep(0.02)
        
        # Mock active processes
        processes = []
        components = ["bot_engine", "data_collector", "order_manager", "risk_monitor"]
        process_types = ["trading", "data", "monitoring", "analysis"]
        
        for i in range(random.randint(5, 12)):
            process = {
                "process_id": f"proc_{1000 + i}",
                "component": random.choice(components),
                "process_type": random.choice(process_types),
                "status": random.choice(["running", "idle", "busy", "waiting"]),
                "cpu_percent": round(random.uniform(1.0, 95.0), 2),
                "memory_mb": random.randint(50, 500),
                "uptime_seconds": random.randint(300, 86400),
                "last_activity": time.time() - random.uniform(0, 300),
                "pid": random.randint(1000, 9999)
            }
            processes.append(process)
        
        return processes

    async def get_system_health(self) -> Dict[str, Any]:
        await asyncio.sleep(0.02)
        
        return {
            "overall_status": random.choice(["healthy", "warning", "critical"]),
            "cpu_usage_percent": round(random.uniform(10.0, 80.0), 2),
            "memory_usage_percent": round(random.uniform(20.0, 70.0), 2),
            "disk_usage_percent": round(random.uniform(15.0, 60.0), 2),
            "active_processes": random.randint(8, 20),
            "failed_processes": random.randint(0, 3),
            "system_load": round(random.uniform(0.5, 3.0), 2),
            "uptime_hours": round(random.uniform(1, 720), 1),
            "last_check": time.time()
        }

    async def get_component_status(self, component: str) -> Dict[str, Any]:
        await asyncio.sleep(0.02)
        
        return {
            "component": component,
            "status": random.choice(["operational", "degraded", "offline"]),
            "active_processes": random.randint(1, 5),
            "error_count": random.randint(0, 10),
            "last_error": time.time() - random.uniform(300, 7200) if random.random() < 0.3 else None,
            "performance_score": round(random.uniform(0.7, 1.0), 3),
            "resource_usage": {
                "cpu": round(random.uniform(5.0, 60.0), 2),
                "memory": round(random.uniform(50.0, 400.0), 2)
            }
        }

    # Streaming Operations
    async def stream_process_health(self) -> AsyncIterator[Dict[str, Any]]:
        print("📡 Streaming process health updates (MOCK)")
        
        for i in range(15):
            await asyncio.sleep(3.0)  # Health updates every 3 seconds
            
            # Mock health update
            event_type = random.choice(["process_started", "process_stopped", 
                                     "high_cpu", "high_memory", "error_detected"])
            
            yield {
                "type": "health_event",
                "event_type": event_type,
                "process_id": f"proc_{random.randint(1001, 1010)}",
                "component": random.choice(["bot_engine", "data_collector", "order_manager"]),
                "severity": random.choice(["info", "warning", "error", "critical"]),
                "message": f"Mock {event_type} event",
                "cpu_percent": round(random.uniform(1.0, 95.0), 2),
                "memory_mb": random.randint(50, 600),
                "timestamp": time.time(),
                "update_id": i
            }

    async def stream_system_metrics(self) -> AsyncIterator[Dict[str, Any]]:
        print("📡 Streaming system metrics (MOCK)")
        
        for i in range(10):
            await asyncio.sleep(5.0)  # Metrics every 5 seconds
            
            yield {
                "type": "system_metrics",
                "cpu_percent": round(random.uniform(10.0, 80.0), 2),
                "memory_percent": round(random.uniform(20.0, 70.0), 2),
                "disk_percent": round(random.uniform(15.0, 60.0), 2),
                "network_in_mb": round(random.uniform(0.1, 10.0), 2),
                "network_out_mb": round(random.uniform(0.1, 5.0), 2),
                "active_connections": random.randint(10, 100),
                "load_average": round(random.uniform(0.2, 3.5), 2),
                "timestamp": time.time(),
                "update_id": i
            }


def fullon_cache_api(ws_url: str = "ws://localhost:8000") -> MockProcessWebSocketAPI:
    return MockProcessWebSocketAPI(ws_url)


async def basic_process_operations(verbose: bool = False) -> bool:
    print("⚙️ === Basic Process WebSocket Operations (MOCK) ===")
    
    try:
        async with fullon_cache_api() as handler:
            # Get active processes
            processes = await handler.get_active_processes()
            print(f"🔄 Retrieved {len(processes)} active processes")
            
            if verbose:
                for proc in processes[:5]:  # Show first 5
                    uptime_hours = proc["uptime_seconds"] / 3600
                    print(f"   ⚙️ {proc['process_id']}: {proc['component']} "
                          f"({proc['status']}) - CPU: {proc['cpu_percent']:.1f}% "
                          f"RAM: {proc['memory_mb']}MB, Up: {uptime_hours:.1f}h")
            
            # Get system health
            health = await handler.get_system_health()
            status_emoji = {"healthy": "✅", "warning": "⚠️", "critical": "🔴"}
            emoji = status_emoji.get(health["overall_status"], "❓")
            
            print(f"   {emoji} System Health: {health['overall_status']}")
            print(f"   📊 CPU: {health['cpu_usage_percent']:.1f}%, "
                  f"RAM: {health['memory_usage_percent']:.1f}%, "
                  f"Load: {health['system_load']}")
            
            # Get component statuses
            components = ["bot_engine", "data_collector", "order_manager"]
            for component in components:
                status = await handler.get_component_status(component)
                status_emoji = {"operational": "🟢", "degraded": "🟡", "offline": "🔴"}
                emoji = status_emoji.get(status["status"], "❓")
                
                if verbose:
                    print(f"   {emoji} {component}: {status['status']} "
                          f"({status['active_processes']} processes, "
                          f"score: {status['performance_score']:.3f})")
            
            print("✅ Process operations completed successfully")
            return True
            
    except Exception as e:
        print(f"❌ Basic process operations failed: {e}")
        return False


async def monitoring_demo(duration: int = 20, verbose: bool = False) -> bool:
    print("📡 === Process Monitoring Streaming Demo (MOCK) ===")
    
    try:
        async with fullon_cache_api() as handler:
            
            async def health_monitor():
                event_count = 0
                async for event in handler.stream_process_health():
                    event_count += 1
                    
                    severity_emoji = {
                        "info": "ℹ️", "warning": "⚠️", 
                        "error": "❌", "critical": "🚨"
                    }
                    emoji = severity_emoji.get(event["severity"], "📋")
                    
                    if verbose:
                        print(f"   {emoji} {event['component']}: {event['event_type']} "
                              f"({event['severity']}) - "
                              f"CPU: {event['cpu_percent']:.1f}%")
                    elif event_count % 3 == 0:
                        print(f"   📊 Health events: {event_count}")
                    
                    if event.get("update_id", 0) >= 6:  # Limit events
                        break
                
                return event_count

            async def metrics_monitor():
                metric_count = 0
                async for metrics in handler.stream_system_metrics():
                    metric_count += 1
                    
                    if verbose:
                        print(f"   📈 System: CPU {metrics['cpu_percent']:.1f}% "
                              f"RAM {metrics['memory_percent']:.1f}% "
                              f"Load {metrics['load_average']:.2f}")
                    elif metric_count % 2 == 0:
                        print(f"   📊 Metric updates: {metric_count}")
                    
                    if metrics.get("update_id", 0) >= 4:  # Limit metrics
                        break
                
                return metric_count
            
            # Run both monitoring streams concurrently
            start_time = time.time()
            health_count, metrics_count = await asyncio.gather(
                health_monitor(),
                metrics_monitor()
            )
            elapsed = time.time() - start_time
            
            print(f"✅ Monitoring completed: {health_count} health events, "
                  f"{metrics_count} metric updates in {elapsed:.1f}s")
            return True
            
    except Exception as e:
        print(f"❌ Process monitoring failed: {e}")
        return False


async def run_demo(args) -> bool:
    print("🚀 fullon_cache_api Process WebSocket Demo (MOCK)")
    print("================================================")
    print("🔧 Will be updated to use real WebSocket server")
    
    results = {}
    
    if args.operations in ["basic", "all"]:
        results["basic"] = await basic_process_operations(args.verbose)
    
    if args.operations in ["monitoring", "all"]:
        results["monitoring"] = await monitoring_demo(args.duration, args.verbose)
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n📊 Success: {success_count}/{total_count} operations")
    return success_count == total_count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operations", choices=["basic", "monitoring", "all"], default="all")
    parser.add_argument("--duration", type=int, default=20, help="Monitoring duration in seconds")
    parser.add_argument("--verbose", "-v", action="store_true")
    
    args = parser.parse_args()
    
    try:
        success = asyncio.run(run_demo(args))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🔄 Demo interrupted")
        sys.exit(1)


if __name__ == "__main__":
    main()