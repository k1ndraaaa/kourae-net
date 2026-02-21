from native.EnvManager.MainClass import *

#Componentes a usar
from adapters.Telegram.MainClass import *
from native.LogManager.Errors import *
from flask import jsonify #type:ignore
from pathlib import Path
import inspect, logging
from native.TimeManager.MainClass import TimeManager
from native.StrikeCounter.MainClass import StrikeCounter

#Referencias
from native.WebResponse.MainClass import WebResponse



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(".../native/LogManager/app.log"),
        logging.FileHandler(".../native/LogManager/error.log"),
    ],
)
log_types = ["info", "error", "warning", "debug"]
info, error, warn, debug = 0, 1, 2, 3

class LogManager:
    def __init__(self):
        # paths
        self.my_relative_path = Path(__file__).resolve().parent.relative_to(root_path)
        self.my_full_path = Path(root_path / self.my_relative_path)

        # env
        self.env = EnvManager().load_vars_from_env(
            Path(self.my_full_path / ".env")
        )

        self.mytelegram = None

        self.mystrikecounter = StrikeCounter(
            limits={
                error: int(self.env.get("errors_attempt_limit", 3)),
                warn: int(self.env.get("warns_attempt_limit", 3)),
            }
        )

        self.mylog = logging.getLogger(self.__class__.__name__)

    def init_adapters(self):
        if self.mytelegram is None:
            self.mytelegram = TelegramNotifier()
    def metainf(self):
        return dict(self.__dict__)

    def logline(
        self,
        *,
        level: int,
        code: str,
        message: str | None = None,
        source: str | None = None,
        debug: str | None = None,
        timestamp: str | None = None,
        include_meta: bool = True
    ) -> tuple[str, str]:

        try:
            level_name = log_types[level].upper()
        except Exception:
            level_name = "UNKNOWN"

        if timestamp is None:
            timestamp = TimeManager().log()

        if source is None:
            frame = inspect.currentframe().f_back
            if frame:
                filename = Path(frame.f_code.co_filename).name
                func = frame.f_code.co_name
                source = f"{filename}:{func}"
            else:
                source = "unknown"

        meta = f"[{level_name} {timestamp} {source}]"

        body = code
        if message:
            body += f" - {message}"
        if debug:
            body += f" | {debug}"

        line = f"{meta} {body}" if include_meta else body
        return line, source

    def log(
        self,
        level: int,
        code: str,
        *,
        message: str | None = None,
        debug: str | None = None,
        source: str | None = None,
        printq: bool = False
    ) -> str:

        try:
            line, source = self.logline(
                level=level,
                code=code,
                message=message,
                debug=debug,
                source=source,
            )
        except Exception as e:
            return ""

        try:
            triggered = self.mystrikecounter.hit(level, source)
        except Exception as e:
            triggered = False

        if triggered:
            try:
                self.mytelegram.send(line)
                print("TELEGRAM SENT")
            except Exception as e:
                print("TELEGRAM ERROR:", e)
        try:
            if level == error:
                self.mylog.error(line)
            elif level == warn:
                self.mylog.warning(line)
            elif level == debug:
                self.mylog.debug(line)
            else:
                self.mylog.info(line)

            if printq:
                logging.info(line)
                print(line)
        except Exception:
            pass

        return line
    
    def http_response(
        self, 
        resp: WebResponse
    ):
        return jsonify(resp.to_dict()), resp.status #type:ignore
    
    def notify_new_user(self, username):
        try:
            self.mytelegram.send(f"¡Se unió un nuevo usuario a Kourae! {username} :)")
        except Exception as e:
            raise LogManagerError(e)

    def delete_new_user(self, username):
        try:
            self.mytelegram.send(f"El usuario {username} se fue de Kourae :(")
        except Exception as e:
            raise LogManagerError(e)
