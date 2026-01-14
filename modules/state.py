import threading
import time

thread_health = {}
thread_health_lock = threading.Lock()


def update_thread_status(thread_name):
    with thread_health_lock:
        thread_health[thread_name] = time.time()


def get_thread_health_snapshot():
    with thread_health_lock:
        return thread_health.copy()
