#!/usr/bin/env python3
"""
Generic Python Cryptocurrency Miner Template

Supports:
- Multi-threaded nonce search
- API challenge fetching
- Auto-retry on errors
- Statistics tracking

Customize:
- API endpoints (get_challenge, submit_nonce)
- Hash algorithm (find_nonce)
- Difficulty calculation
"""

import requests
import hashlib
import time
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

class CryptoMiner:
    def __init__(self, cookie, threads=2):
        self.cookie = cookie
        self.threads = threads
        self.base_url = "https://api.example.com"  # CUSTOMIZE
        self.session = requests.Session()
        self.session.headers.update({
            'Cookie': cookie,
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        self.stats = {
            'blocks_mined': 0,
            'errors': 0,
            'start_time': time.time()
        }
        self.lock = threading.Lock()
    
    def log(self, msg, level="INFO"):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] [{level}] {msg}", flush=True)
    
    def get_challenge(self):
        """Fetch mining challenge from API"""
        try:
            resp = self.session.post(f"{self.base_url}/challenge", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # CUSTOMIZE: Extract challenge fields
                return data.get('challenge_id'), data.get('nonce_prefix'), data.get('difficulty_bits', 25)
            else:
                self.log(f"Failed to get challenge: {resp.status_code}", "ERROR")
                return None, None, None
        except Exception as e:
            self.log(f"Challenge error: {e}", "ERROR")
            return None, None, None
    
    def find_nonce(self, nonce_prefix, difficulty, start_nonce, end_nonce):
        """
        Find valid nonce for challenge
        
        CUSTOMIZE THIS METHOD based on your mining algorithm:
        - SHA256 with trailing zeros (Bitcoin-style)
        - Scrypt (Litecoin-style)
        - Ethash (Ethereum-style)
        - Custom hash function
        """
        # Example: SHA256 with trailing zero bits (rpow2-style)
        prefix_bytes = bytes.fromhex(nonce_prefix)
        
        for nonce in range(start_nonce, end_nonce):
            # Create hash: prefix + nonce (little endian)
            data = prefix_bytes + nonce.to_bytes(8, byteorder='little')
            hash_result = hashlib.sha256(data).digest()
            
            # Count trailing zero bits
            trailing_zeros = 0
            for byte in reversed(hash_result):
                if byte == 0:
                    trailing_zeros += 8
                else:
                    trailing_zeros += (byte & -byte).bit_length() - 1
                    break
            
            if trailing_zeros >= difficulty:
                return nonce
        
        return None
    
    def submit_nonce(self, challenge_id, nonce):
        """Submit found nonce to API"""
        try:
            payload = {
                'challenge_id': challenge_id,
                'solution_nonce': str(nonce)
            }
            resp = self.session.post(f"{self.base_url}/mint", json=payload, timeout=10)
            
            if resp.status_code == 200:
                return True, "Minted!"
            else:
                return False, f"Failed ({resp.status_code})"
        except Exception as e:
            return False, f"Error: {e}"
    
    def mine_block(self):
        """Mine a single block"""
        # Get challenge
        challenge_id, nonce_prefix, difficulty = self.get_challenge()
        if not challenge_id:
            with self.lock:
                self.stats['errors'] += 1
            return False
        
        self.log(f"Challenge: {challenge_id[:16]}... | Diff: {difficulty}")
        
        # Find nonce with multi-threading
        start_time = time.time()
        chunk_size = 100_000_000  # 100M nonces per thread
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = []
            for i in range(self.threads):
                start = i * chunk_size
                end = start + chunk_size
                future = executor.submit(self.find_nonce, nonce_prefix, difficulty, start, end)
                futures.append(future)
            
            # Wait for first valid nonce
            for future in as_completed(futures):
                nonce = future.result()
                if nonce is not None:
                    # Cancel other threads
                    for f in futures:
                        f.cancel()
                    
                    elapsed = time.time() - start_time
                    self.log(f"Nonce: {nonce} in {elapsed:.2f}s")
                    
                    # Submit nonce
                    success, msg = self.submit_nonce(challenge_id, nonce)
                    if success:
                        with self.lock:
                            self.stats['blocks_mined'] += 1
                        self.log(f"✓ {msg} | Total: {self.stats['blocks_mined']}", "SUCCESS")
                        return True
                    else:
                        self.log(msg, "ERROR")
                        with self.lock:
                            self.stats['errors'] += 1
                        return False
        
        self.log("No nonce found in range", "WARN")
        return False
    
    def run(self):
        """Main mining loop"""
        self.log(f"Starting miner with {self.threads} threads")
        
        while True:
            try:
                self.mine_block()
                time.sleep(1)  # Small delay between blocks
            except KeyboardInterrupt:
                self.log("Mining stopped by user", "INFO")
                self.print_stats()
                break
            except Exception as e:
                self.log(f"Error: {e}", "ERROR")
                with self.lock:
                    self.stats['errors'] += 1
                time.sleep(5)
    
    def print_stats(self):
        """Print mining statistics"""
        elapsed = time.time() - self.stats['start_time']
        hours = elapsed / 3600
        blocks_per_hour = self.stats['blocks_mined'] / hours if hours > 0 else 0
        
        print("\n" + "="*50)
        print("Mining Statistics")
        print("="*50)
        print(f"Blocks mined: {self.stats['blocks_mined']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Runtime: {elapsed/60:.1f} minutes")
        print(f"Rate: {blocks_per_hour:.1f} blocks/hour")
        print("="*50 + "\n")


def main():
    # Read cookie from config file
    try:
        with open('config.txt', 'r') as f:
            cookie = f.read().strip()
    except FileNotFoundError:
        print("ERROR: config.txt not found!")
        print("Create config.txt with your session cookie")
        sys.exit(1)
    
    # Get threads from command line or auto-detect
    threads = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    
    # Start miner
    miner = CryptoMiner(cookie, threads=threads)
    miner.run()


if __name__ == "__main__":
    main()
