import logging, inspect, os
from pathlib import Path
from typing import Optional
from native.EnvLoader.MainClass import EnvLoader
from native.TimeManager.MainClass import TimeManager
from native.Library.commons import StrikeCounter, Session
from native.LogManager.Errors import LogManagerError
from adapters.Telegram.MainClass import TelegramNotifier

LOG_INFO, LOG_ERROR, LOG_WARN, LOG_DEBUG = 0, 1, 2, 3
log_types = ["info", "error", "warning", "debug"]

class LogManager:
    def __init__(self, config_path: Path, strike_counter: StrikeCounter):
        self.env = EnvLoader().load_vars_from_env(config_path)
        self.my_full_path = Path(f"/home/{os.environ['USER']}/")
        self.strike_counter = strike_counter
        self.logger = logging.getLogger("LogManager")
        self.logger.setLevel(logging.INFO)
        log_file = self.my_full_path / "app.log"
        error_file = self.my_full_path / "error.log"
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        file_handler_info = logging.FileHandler(log_file)
        file_handler_info.setLevel(logging.INFO)
        file_handler_info.setFormatter(formatter)
        file_handler_error = logging.FileHandler(error_file)
        file_handler_error.setLevel(logging.ERROR)
        file_handler_error.setFormatter(formatter)
        self.logger.addHandler(file_handler_info)
        self.logger.addHandler(file_handler_error)
        self.telegram: Optional[TelegramNotifier] = None
    def init_telegram(self):
        if self.telegram is None:
            self.telegram = TelegramNotifier()
    def _get_source(self):
        frame = inspect.currentframe().f_back
        if frame:
            filename = Path(frame.f_code.co_filename).name
            func = frame.f_code.co_name
            return f"{filename}:{func}"
        return "unknown"
    def log(
        self,
        level: int,
        code: str,
        *,
        message: Optional[str] = None,
        debug: Optional[str] = None,
        session: Optional[Session] = None,
        printq: bool = False
    ) -> str:
        timestamp = TimeManager().log()
        source = self._get_source()
        level_name = log_types[level] if level < len(log_types) else "UNKNOWN"
        body = f"{code}"
        if message:
            body += f" - {message}"
        if debug:
            body += f" | {debug}"
        line = f"[{level_name.upper()} {timestamp} {source}] {body}"
        triggered = False
        if self.strike_counter and session:
            triggered = self.strike_counter.hit(level, session)
        if triggered and self.telegram:
            try:
                self.telegram.send(line)
            except Exception:
                pass
        if level == LOG_ERROR:
            self.logger.error(line)
        elif level == LOG_WARN:
            self.logger.warning(line)
        elif level == LOG_DEBUG:
            self.logger.debug(line)
        else:
            self.logger.info(line)
        if printq:
            print(line)
        return line
    def notify_new_user(self, username: str):
        if self.telegram:
            try:
                self.telegram.send(f"¡Nuevo usuario en Kourae: {username}!")
            except Exception as e:
                raise LogManagerError(e)