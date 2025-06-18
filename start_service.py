#!/usr/bin/env python3
# start_service.py - Simple service starter for testing

import subprocess
import sys
import time
import os

def start_user_service():
    """Start the user service for testing"""
    print("🚀 Starting user_service for testing...")
    
    # Change to user_service directory
    os.chdir("/home/stocksadmin/stocksblitz/user_service")
    
    try:
        # Start the service
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        print("📝 Service starting... (Press Ctrl+C to stop)")
        print("🌐 Service will be available at: http://localhost:8002")
        print("🏥 Health check: http://localhost:8002/health")
        print("📊 Integration status: http://localhost:8002/health/integrations")
        print("=" * 60)
        
        # Stream output
        for line in process.stdout:
            print(line.rstrip())
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping service...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        print("✅ Service stopped")
        
    except Exception as e:
        print(f"❌ Error starting service: {e}")

if __name__ == "__main__":
    start_user_service()