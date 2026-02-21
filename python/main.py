import datetime
import json
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
    "y": 0,
    "mo": 0,
    "d": 0,
    "running": True,
    "timezone": "Europe/Paris",
    "hour_mode": 24,  # 24 or 12
}

# Used to avoid sending clearMatrix repeatedly
_matrix_is_on = True

# Small persistent config file (same folder as this script)
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

# Default timezone if config is missing/invalid
_DEFAULT_TZ = "Europe/Paris"


def _load_config() -> dict:
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        tz = str(cfg.get("timezone", _DEFAULT_TZ))
        hm = int(cfg.get("hour_mode", 24))
        if hm not in (12, 24):
            hm = 24
        return {"timezone": tz, "hour_mode": hm}
    except Exception:
        return {"timezone": _DEFAULT_TZ, "hour_mode": 24}


def _save_config(tz_name: str, hour_mode: int) -> None:
    try:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"timezone": tz_name, "hour_mode": hour_mode}, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save config.json: {e}")


def _is_valid_tz(tz_name: str) -> bool:
    try:
        return tz_name in available_timezones()
    except Exception:
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


def _hour_for_display(h24: int, hour_mode: int) -> int:
    if hour_mode == 12:
        h = h24 % 12
        if h == 0:
            h = 12
        return h
    return h24


def api_get_hour_mode(_req=None):
    with _lock:
        return {"hour_mode": _state.get("hour_mode", 24)}


def api_set_hour_mode(mode=None, _req=None):
    try:
        m = int(mode) if mode is not None else 0
        if m not in (12, 24):
            return {"ok": False, "error": "mode must be 12 or 24"}

        with _lock:
            _state["hour_mode"] = m
            tz_name = _state["timezone"]

        _save_config(tz_name, m)
        logger.info(f"Hour mode set to {m}h")
        return {"ok": True, "hour_mode": m}
    except Exception as e:
        logger.error(f"api_set_hour_mode exception: {e}")
        return {"ok": False, "error": f"Exception: {e}"}


def _tick_loop():
    global _matrix_is_on

    while True:
        tz = _get_tz()
        now = datetime.datetime.now(tz=tz)

        y = now.year
        mo = now.month
        d = now.day
        h = now.hour
        m = now.minute
        s = now.second

        with _lock:
            _state["h"] = h
            _state["m"] = m
            _state["s"] = s
            _state["y"] = y
            _state["mo"] = mo
            _state["d"] = d
            running = _state["running"]
            hour_mode = _state.get("hour_mode", 24)

        if running:
            _matrix_is_on = True
            try:
                h_send = _hour_for_display(h, hour_mode)
                Bridge.call("updateTime", h_send, m, s)
                logger.info(f"Sent time {h_send:02d}:{m:02d}:{s:02d} (mode {hour_mode}h, {tz.key})")
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
            "y": _state["y"],
            "mo": _state["mo"],
            "d": _state["d"],
            "running": _state["running"],
            "timezone": _state["timezone"],
            "hour_mode": _state.get("hour_mode", 24),
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
            hm = _state.get("hour_mode", 24)

        _save_config(tz_name, hm)
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

web.expose_api("GET", "/api/hour_mode", api_get_hour_mode)
web.expose_api("POST", "/api/hour_mode", api_set_hour_mode)


def main():
    cfg = _load_config()
    tz0 = cfg["timezone"]
    hm0 = cfg["hour_mode"]

    if _is_valid_tz(tz0):
        with _lock:
            _state["timezone"] = tz0
    else:
        with _lock:
            _state["timezone"] = _DEFAULT_TZ

    with _lock:
        _state["hour_mode"] = hm0

    logger.info(f"Python main() started, timezone={_state['timezone']}, hour_mode={_state['hour_mode']}")

    t = threading.Thread(target=_tick_loop, daemon=True)
    t.start()
    App.run()


if __name__ == "__main__":
    main()
