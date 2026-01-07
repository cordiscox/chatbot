import logging, time, traceback, orjson

class JSONFormatter(logging.Formatter):
    def format(self, record):
        # Base payload
        payload = {
            "ts": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Include exception if present
        if record.exc_info:
            payload["exc"] = traceback.format_exception(*record.exc_info)

        # Merge any structured fields passed via `extra=` into the log record.
        # Avoid clobbering reserved attributes.
        reserved = set(list(record.__dict__.keys()))
        # Common attributes that are not custom extras
        common = {"name", "msg", "args", "levelname", "levelno", "pathname", "filename", "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process"}
        for k, v in record.__dict__.items():
            if k in common:
                continue
            try:
                payload[k] = v
            except Exception:
                payload[k] = str(v)

        # orjson.dumps -> bytes
        return orjson.dumps(payload).decode()

def setup_logging(level=logging.INFO):
    root = logging.getLogger()
    if not root.handlers:
        h = logging.StreamHandler()
        h.setFormatter(JSONFormatter())
        root.addHandler(h)
    root.setLevel(level)