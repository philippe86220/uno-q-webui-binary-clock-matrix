import datetime
import json
from urllib.parse import parse_qs
import os
import threading
import time
from zoneinfo import ZoneInfo, available_timezones

from arduino.app_utils import App, Bridge, Logger
from arduino.app_bricks.web_ui import WebUI

logger = Logger("uno-q-clock")
print("Python ready", flush=True)

web = WebUI()  # serves ./assets/index.html automatically

_lock = threading.Lock()
_state = {
    "h": 0,
    "m": 0,
    "s": 0,
    "running": True,
    "timezone": "Europe/Paris",
}

# Used to avoid sending clearMatrix repeatedly
_matrix_is_on = True

# Small persistent config file (same folder as this script)
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

# Default timezone if config is missing/invalid
_DEFAULT_TZ = "Europe/Paris"


def _load_config_timezone() -> str:
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        tz = str(cfg.get("timezone", _DEFAULT_TZ))
        return tz
    except Exception:
        return _DEFAULT_TZ


def _save_config_timezone(tz_name: str) -> None:
    try:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"timezone": tz_name}, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save config.json: {e}")


def _is_valid_tz(tz_name: str) -> bool:
    # available_timezones() may be heavy but fine for occasional calls
    try:
        return tz_name in available_timezones()
    except Exception:
        # Fallback: try to construct ZoneInfo
        try:
            ZoneInfo(tz_name)
            return True
        except Exception:
            return False


def _get_tz() -> ZoneInfo:
    with _lock:
        tz_name = _state["timezone"]
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo(_DEFAULT_TZ)


def _tick_loop():
    global _matrix_is_on

    while True:
        tz = _get_tz()
        now = datetime.datetime.now(tz=tz)

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
                logger.info(f"Sent time {h:02d}:{m:02d}:{s:02d} ({tz.key})")
            except Exception as e:
                logger.error(f"Bridge updateTime error: {e}")
        else:
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
            "timezone": _state["timezone"],
        }


def api_start(_req=None):
    with _lock:
        _state["running"] = True
    return {"ok": True}


def api_stop(_req=None):
    with _lock:
        _state["running"] = False
    return {"ok": True}


def api_get_timezone(_req=None):
    with _lock:
        return {"timezone": _state["timezone"]}

def api_set_timezone(timezone=None, _req=None):
    try:
        tz_name = (timezone or "").strip()

        if not tz_name:
            return {"ok": False, "error": "Missing 'timezone' field"}

        if not _is_valid_tz(tz_name):
            return {"ok": False, "error": f"Invalid timezone '{tz_name}' (use IANA format like 'Asia/Dhaka')"}

        with _lock:
            _state["timezone"] = tz_name

        _save_config_timezone(tz_name)
        logger.info(f"Timezone set to {tz_name}")
        return {"ok": True, "timezone": tz_name}

    except Exception as e:
        logger.error(f"api_set_timezone exception: {e}")
        return {"ok": False, "error": f"Exception: {e}"}

web.expose_api("GET", "/api/time", api_time)
web.expose_api("POST", "/api/start", api_start)
web.expose_api("POST", "/api/stop", api_stop)

web.expose_api("GET", "/api/timezone", api_get_timezone)
web.expose_api("POST", "/api/timezone", api_set_timezone)


def main():
    # Load timezone at boot
    tz0 = _load_config_timezone()
    if _is_valid_tz(tz0):
        with _lock:
            _state["timezone"] = tz0
    else:
        with _lock:
            _state["timezone"] = _DEFAULT_TZ

    logger.info(f"Python main() started, timezone={_state['timezone']}")
    t = threading.Thread(target=_tick_loop, daemon=True)
    t.start()
    App.run()


if __name__ == "__main__":
    main()
