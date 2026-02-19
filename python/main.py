import datetime
import threading
import time
from zoneinfo import ZoneInfo

from arduino.app_utils import App, Bridge, Logger
from arduino.app_bricks.web_ui import WebUI

TZ_FR = ZoneInfo("Europe/Paris")
logger = Logger("uno-q-clock")

print("Python ready", flush=True)

web = WebUI()  # serves ./assets/index.html automatically

_lock = threading.Lock()
_state = {
    "h": 0,
    "m": 0,
    "s": 0,
    "running": True,
}

# Used to avoid sending clearMatrix repeatedly
_matrix_is_on = True

def _tick_loop():
    global _matrix_is_on

    while True:
        now = datetime.datetime.now(tz=TZ_FR)
        h = now.hour
        m = now.minute
        s = now.second

        with _lock:
            _state["h"] = h
            _state["m"] = m
            _state["s"] = s
            running = _state["running"]

        if running:
            _matrix_is_on = True
            try:
                Bridge.call("updateTime", h, m, s)
                logger.info(f"Sent time {h:02d}:{m:02d}:{s:02d}")
            except Exception as e:
                logger.error(f"Bridge updateTime error: {e}")
        else:
            # Turn off LEDs only once when stopping
            if _matrix_is_on:
                try:
                    Bridge.call("clearMatrix")
                    logger.info("Matrix cleared")
                except Exception as e:
                    logger.error(f"Bridge clearMatrix error: {e}")
                _matrix_is_on = False

        time.sleep(1)

def api_time(_req=None):
    with _lock:
        return {
            "h": _state["h"],
            "m": _state["m"],
            "s": _state["s"],
            "running": _state["running"],
        }

def api_start(_req=None):
    with _lock:
        _state["running"] = True
    return {"ok": True}

def api_stop(_req=None):
    with _lock:
        _state["running"] = False
    return {"ok": True}

web.expose_api("GET", "/api/time", api_time)
web.expose_api("POST", "/api/start", api_start)
web.expose_api("POST", "/api/stop", api_stop)

def main():
    logger.info("Python main() started")
    t = threading.Thread(target=_tick_loop, daemon=True)
    t.start()
    App.run()

if __name__ == "__main__":
    main()
