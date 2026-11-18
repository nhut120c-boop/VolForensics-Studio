"""
VolForensics Studio - Desktop & Web GUI Launcher
Runs local FastAPI server and opens browser automatically.
"""

import sys
import os
import time
import socket
import webbrowser
import threading

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def find_free_port(start_port: int = 8888) -> int:
    port = start_port
    while is_port_in_use(port):
        port += 1
    return port

def open_browser(url: str, delay_seconds: float = 1.2):
    def _open():
        time.sleep(delay_seconds)
        print(f"\n[+] Opening browser at: {url}")
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    try:
        import uvicorn
        import fastapi
        import psutil
    except ImportError as exc:
        print(f'Thieu thu vien: {exc}. Chay: python -m pip install -r requirements-gui.txt')
        return 1
    print("=" * 65)
    print("        VolForensics Studio - Memory Forensics UI        ")
    print("=" * 65)
    print("[*] Initializing Volatility Forensic Workstation...")
    
    # Check Python environment
    port = find_free_port(8888)
    url = f"http://127.0.0.1:{port}"
    
    print(f"[+] Server starting on: {url}")
    print("[*] Launching browser window...")
    open_browser(url)
    
    try:
        # Import and run uvicorn
        uvicorn.run("app.main:app", host="127.0.0.1", port=port, log_level="warning")
    except KeyboardInterrupt:
        print("\n[*] Shutting down VolForensics Studio. Goodbye!")

if __name__ == "__main__":
    sys.exit(main() or 0)
