#!/usr/bin/env python3
"""
Multi-Worker Browser Automation Template
Parallel registration/scraping with async workers

Usage:
    python multi_worker.py

Features:
    - 10 chromium parallel (configurable)
    - Progress tracking per worker
    - Batch OTP/2FA input
    - Auto screenshot on completion
    - Summary report

Requirements:
    pip install cloakbrowser
"""

import asyncio
import cloakbrowser
import sys
from datetime import datetime

# Config
MAX_WORKERS = 10  # Adjust based on RAM (500MB per worker)
HEADLESS = False  # Set True for production
PROXY_SERVER = "proxy.example.com:8080"
PROXY_USER = "username"
PROXY_PASS = "password"

class Worker:
    def __init__(self, worker_id, data):
        self.worker_id = worker_id
        self.data = data  # e.g., phone number, email, etc.
        self.browser = None
        self.page = None
        self.status = "pending"
        self.error = None
        self.result = None
        
    async def log(self, message):
        """Log with worker ID and timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [Worker-{self.worker_id}] {message}")
    
    async def run(self):
        """Main worker logic - customize this"""
        try:
            self.status = "running"
            await self.log(f"Starting for {self.data}")
            
            # Launch browser
            self.browser = await cloakbrowser.launch_async(
                headless=HEADLESS,
                proxy={
                    'server': f'http://{PROXY_SERVER}',
                    'username': PROXY_USER,
                    'password': PROXY_PASS
                }
            )
            
            self.page = await self.browser.new_page()
            
            # Example: Navigate and fill form
            await self.page.goto('https://example.com/register')
            await asyncio.sleep(2)
            
            # Fill form
            await self.page.fill('input[name="email"]', self.data)
            await self.page.click('button[type="submit"]')
            await asyncio.sleep(2)
            
            # Wait for OTP stage
            self.status = "waiting_otp"
            await self.log("OTP sent, waiting for input...")
            
            # OTP will be set externally by main()
            while not hasattr(self, 'otp'):
                await asyncio.sleep(1)
            
            # Continue with OTP
            await self.page.fill('input[name="otp"]', self.otp)
            await self.page.click('button[type="submit"]')
            await asyncio.sleep(3)
            
            # Screenshot result
            screenshot_path = f'result_{self.worker_id}.png'
            await self.page.screenshot(path=screenshot_path)
            
            self.status = "success"
            self.result = screenshot_path
            await self.log(f"✅ Success! Screenshot: {screenshot_path}")
            return True
            
        except Exception as e:
            self.status = "failed"
            self.error = str(e)
            await self.log(f"❌ Error: {e}")
            return False
        
        finally:
            if self.browser:
                await self.browser.close()

async def main():
    print("=" * 60)
    print("MULTI-WORKER AUTOMATION")
    print("=" * 60)
    print(f"⚙️ Max Workers: {MAX_WORKERS}")
    print(f"🌐 Headless: {HEADLESS}")
    print("=" * 60)
    
    # Input data (customize this)
    print("\n📝 Enter data (one per line, 'done' to finish):")
    data_list = []
    while True:
        item = input(f"   Item #{len(data_list)+1}: ").strip()
        if item.lower() == 'done':
            break
        if item:
            data_list.append(item)
            print(f"   ✅ Added: {item}")
        if len(data_list) >= MAX_WORKERS:
            print(f"\n   ⚠️ Reached limit of {MAX_WORKERS}")
            break
    
    if not data_list:
        print("❌ No data provided!")
        return
    
    print(f"\n✅ Total items: {len(data_list)}")
    input("\nPress ENTER to start...")
    
    # Create workers
    workers = [Worker(i+1, data) for i, data in enumerate(data_list)]
    
    # Launch workers
    print(f"\n{'='*60}")
    print("🚀 STARTING WORKERS...")
    print(f"{'='*60}\n")
    
    tasks = [asyncio.create_task(w.run()) for w in workers[:MAX_WORKERS]]
    
    # Wait for all to reach OTP stage
    print("\n⏳ Waiting for all workers to reach OTP stage...")
    while True:
        waiting = sum(1 for w in workers if w.status == "waiting_otp")
        if waiting == len(workers[:MAX_WORKERS]):
            break
        await asyncio.sleep(1)
    
    print(f"\n✅ All workers ready for OTP!")
    print(f"\n{'='*60}")
    print("📱 INPUT OTP FOR EACH WORKER")
    print(f"{'='*60}")
    
    # Collect OTP for each worker
    for worker in workers[:MAX_WORKERS]:
        if worker.status == "waiting_otp":
            otp = input(f"\n✉️ OTP for {worker.data}: ").strip()
            worker.otp = otp
            print(f"   ✅ OTP set for Worker-{worker.worker_id}")
    
    # Wait for completion
    print(f"\n{'='*60}")
    print("⏳ Completing tasks...")
    print(f"{'='*60}\n")
    
    await asyncio.gather(*tasks)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    
    success = sum(1 for w in workers if w.status == "success")
    failed = sum(1 for w in workers if w.status == "failed")
    
    print(f"✅ Success: {success}")
    print(f"❌ Failed: {failed}")
    print(f"📝 Total: {len(workers[:MAX_WORKERS])}")
    
    print(f"\n{'='*60}")
    print("DETAILS:")
    print(f"{'='*60}")
    
    for worker in workers[:MAX_WORKERS]:
        icon = "✅" if worker.status == "success" else "❌"
        print(f"{icon} Worker-{worker.worker_id}: {worker.data} - {worker.status.upper()}")
        if worker.error:
            print(f"   Error: {worker.error}")
        if worker.result:
            print(f"   Result: {worker.result}")
    
    print(f"\n{'='*60}")
    print("✅ ALL DONE!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Cancelled by user")
        sys.exit(0)
