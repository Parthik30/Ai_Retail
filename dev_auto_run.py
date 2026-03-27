#!/usr/bin/env python3
"""
dev_auto_run.py - watches for source changes, runs pytest, and restarts Streamlit when tests pass.

Usage:
  python dev_auto_run.py

Requires: watchdog (pip install watchdog)
"""

import os
import sys
import time
import subprocess
import threading

try:
    from watchdog.observers import Observer
    from watchdog.events import PatternMatchingEventHandler
except Exception:
    print("Missing dependency 'watchdog'. Install with: pip install watchdog")
    sys.exit(1)

WATCH_PATTERNS = ["*.py", "*.csv", "*.yml", "*.yaml"]
WATCH_IGNORE = ["*/.venv/*", "*/.git/*", "*/__pycache__/*"]

PYTEST_CMD = [sys.executable, "-m", "pytest", "-q"]
STREAMLIT_CMD = [sys.executable, "-m", "streamlit", "run", "backend/streamlit_app/app.py", "--server.port", "8501", "--server.address", "127.0.0.1"]

class ChangeHandler(PatternMatchingEventHandler):
    def __init__(self, restart_callback):
        super().__init__(patterns=WATCH_PATTERNS, ignore_patterns=WATCH_IGNORE, ignore_directories=False, case_sensitive=False)
        self.restart_callback = restart_callback
        self._last = 0

    def on_any_event(self, event):
        # simple debounce
        now = time.time()
        if now - self._last < 0.8:
            return
        self._last = now
        print(f"Detected change: {event.src_path}. Running tests...")
        threading.Thread(target=self.restart_callback).start()


def run_pytest():
    p = subprocess.run(PYTEST_CMD, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(p.stdout)
    return p.returncode == 0


def start_streamlit():
    print("Starting Streamlit...")
    proc = subprocess.Popen(STREAMLIT_CMD, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    # simple thread to echo output
    def relay():
        try:
            for line in proc.stdout:
                print(line, end='')
        except Exception:
            pass
    threading.Thread(target=relay, daemon=True).start()
    return proc


def stop_streamlit(proc):
    if proc and proc.poll() is None:
        print("Stopping Streamlit...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    return None


def restart_proc(proc_container):
    ok = run_pytest()
    if ok:
        print("Tests passed. Restarting Streamlit...")
        proc_container[0] = stop_streamlit(proc_container[0])
        time.sleep(0.5)
        proc_container[0] = start_streamlit()
    else:
        print("Tests failed. Not restarting Streamlit.")


def main():
    proc_container = [start_streamlit()]
    event_handler = ChangeHandler(lambda: restart_proc(proc_container))
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.start()
    print("Watching for file changes. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping watcher...")
        observer.stop()
        stop_streamlit(proc_container[0])
    observer.join()


if __name__ == "__main__":
    main()
