import sys
import os
import subprocess
import time
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

def main():
    print("=" * 80)
    print("           INSIGHTX AI DATA PLATFORM - UNIFIED LAUNCHER")
    print("=" * 80)
    
    python_exe = sys.executable
    
    # 1. Start FastAPI Backend Server
    print("\n[1/3] Starting FastAPI Backend on http://127.0.0.1:8000 ...")
    backend_cmd = [python_exe, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
    backend_proc = subprocess.Popen(backend_cmd, cwd=BASE_DIR)
    
    # 2. Start Vite Frontend Server
    print("[2/3] Starting Vite Frontend UI on http://localhost:5173 ...")
    frontend_cmd = "npm run dev"
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=FRONTEND_DIR, shell=True)
    
    time.sleep(3)
    
    # 3. Open Browser
    print("[3/3] Platform Ready! Opening http://localhost:5173 in browser ...\n")
    try:
        webbrowser.open("http://localhost:5173")
    except Exception:
        pass
        
    print("Press Ctrl+C in this window to stop both servers.")
    try:
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down InsightX platform services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
