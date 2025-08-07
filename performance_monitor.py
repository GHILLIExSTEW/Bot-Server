#!/usr/bin/env python3
"""
Performance Monitoring Dashboard
Shows real-time performance metrics for DBSBM services
"""

import time
import psutil
import requests
import asyncio
import aiohttp
from datetime import datetime
import threading
import json

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'discord_auth_time': [],
            'database_query_time': [],
            'page_load_time': [],
            'memory_usage': [],
            'cpu_usage': []
        }
        
    async def test_discord_auth_speed(self):
        """Test Discord OAuth speed"""
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                # Test Discord API connectivity
                async with session.get('https://discord.com/api/v10/gateway') as response:
                    if response.status == 200:
                        auth_time = time.time() - start_time
                        self.metrics['discord_auth_time'].append(auth_time)
                        return auth_time
        except Exception as e:
            print(f"Discord auth test error: {e}")
            return None
    
    def test_web_performance(self):
        """Test web page performance"""
        try:
            start_time = time.time()
            response = requests.get('http://localhost:5000/', timeout=10)
            load_time = time.time() - start_time
            
            if response.status_code == 200:
                self.metrics['page_load_time'].append(load_time)
                return load_time
        except Exception as e:
            print(f"Web performance test error: {e}")
            return None
    
    def monitor_system_resources(self):
        """Monitor system resources"""
        # CPU usage
        cpu = psutil.cpu_percent(interval=1)
        self.metrics['cpu_usage'].append(cpu)
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.metrics['memory_usage'].append(memory.percent)
        
        return cpu, memory.percent
    
    def get_performance_summary(self):
        """Get performance summary"""
        summary = {}
        
        for metric, values in self.metrics.items():
            if values:
                summary[metric] = {
                    'avg': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'latest': values[-1] if values else 0,
                    'count': len(values)
                }
            else:
                summary[metric] = {
                    'avg': 0, 'min': 0, 'max': 0, 'latest': 0, 'count': 0
                }
        
        return summary
    
    def display_dashboard(self):
        """Display performance dashboard"""
        print("\n" + "="*60)
        print("🚀 DBSBM PERFORMANCE DASHBOARD")
        print("="*60)
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        summary = self.get_performance_summary()
        
        print(f"\n📊 PERFORMANCE METRICS:")
        print("-"*40)
        
        # Discord Auth Performance
        discord_avg = summary['discord_auth_time']['avg']
        print(f"🔗 Discord Auth:     {discord_avg:.3f}s avg")
        
        # Page Load Performance  
        page_avg = summary['page_load_time']['avg']
        print(f"🌐 Page Load:        {page_avg:.3f}s avg")
        
        # System Resources
        cpu_avg = summary['cpu_usage']['avg']
        mem_avg = summary['memory_usage']['avg']
        print(f"💻 CPU Usage:        {cpu_avg:.1f}% avg")
        print(f"🧠 Memory Usage:     {mem_avg:.1f}% avg")
        
        # Performance Rating
        print(f"\n⭐ PERFORMANCE RATING:")
        print("-"*40)
        
        if discord_avg < 1.0:
            print("🟢 Discord Auth: EXCELLENT (< 1s)")
        elif discord_avg < 2.0:
            print("🟡 Discord Auth: GOOD (< 2s)")
        else:
            print("🔴 Discord Auth: NEEDS IMPROVEMENT (> 2s)")
        
        if page_avg < 0.5:
            print("🟢 Page Load: EXCELLENT (< 0.5s)")
        elif page_avg < 2.0:
            print("🟡 Page Load: GOOD (< 2s)")
        else:
            print("🔴 Page Load: NEEDS IMPROVEMENT (> 2s)")
        
        if cpu_avg < 50:
            print("🟢 CPU Usage: EXCELLENT (< 50%)")
        elif cpu_avg < 80:
            print("🟡 CPU Usage: MODERATE (< 80%)")
        else:
            print("🔴 CPU Usage: HIGH (> 80%)")
        
        print("\n" + "="*60)

async def run_performance_tests():
    """Run continuous performance tests"""
    monitor = PerformanceMonitor()
    
    print("🔍 Starting Performance Monitoring...")
    print("📈 Running tests every 30 seconds")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        while True:
            # Test Discord auth speed
            discord_time = await monitor.test_discord_auth_speed()
            
            # Test web performance
            web_time = monitor.test_web_performance()
            
            # Monitor system resources
            cpu, memory = monitor.monitor_system_resources()
            
            # Display dashboard
            monitor.display_dashboard()
            
            # Performance recommendations
            summary = monitor.get_performance_summary()
            
            print("\n💡 OPTIMIZATION SUGGESTIONS:")
            print("-"*40)
            
            if summary['discord_auth_time']['avg'] > 2.0:
                print("• Enable async Discord OAuth")
                print("• Implement connection pooling")
                
            if summary['page_load_time']['avg'] > 2.0:
                print("• Enable Redis caching")
                print("• Optimize database queries")
                
            if summary['cpu_usage']['avg'] > 70:
                print("• Reduce background processes")
                print("• Optimize service threads")
                
            if summary['memory_usage']['avg'] > 80:
                print("• Check for memory leaks")
                print("• Restart services periodically")
            
            # Wait before next test
            await asyncio.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Performance monitoring stopped")
        
        # Final summary
        print("\n📊 FINAL PERFORMANCE SUMMARY:")
        print("="*50)
        final_summary = monitor.get_performance_summary()
        
        for metric, stats in final_summary.items():
            if stats['count'] > 0:
                print(f"{metric}: {stats['avg']:.3f}s avg ({stats['count']} samples)")

if __name__ == "__main__":
    asyncio.run(run_performance_tests())
