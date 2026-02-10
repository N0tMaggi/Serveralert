import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from modules import runtime as runtime_mod, state

SCRIPT_START_TIME = time.time()


class HealthRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path not in ("/", "/health"):
            self.send_error(404, "Not Found")
            return

        now = time.time()
        snapshot = state.get_thread_health_snapshot()
        response = {
            "uptime_seconds": int(now - SCRIPT_START_TIME),
            "threads": []
        }

        for name, timestamp in snapshot.items():
            response["threads"].append({
                "name": name,
                "seconds_since_last_run": round(now - timestamp, 2)
            })

        response["threads"].sort(key=lambda entry: entry["name"])

        payload = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def start_health_server():
    runtime = runtime_mod.get_runtime()
    config_data = runtime.config
    health_config = config_data.get("health_server", {})
    if not health_config.get("enabled", False):
        return

    host = health_config.get("host", "127.0.0.1")
    port = int(health_config.get("port", 8765))
    server = ThreadingHTTPServer((host, port), HealthRequestHandler)
    print(f"Health endpoint available at http://{host}:{port}/health")
    server.timeout = 1
    try:
        while True:
            state.update_thread_status("Health Server")
            server.handle_request()
    except Exception as exc:
        from modules import logger

        logger.log(f"Health server stopped: {exc}")
