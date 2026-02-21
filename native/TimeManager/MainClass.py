from datetime import datetime
from zoneinfo import ZoneInfo

class TimeManager:
    UTC = ZoneInfo("UTC")
    def epoch(cls, tz: ZoneInfo = None) -> int:
        tz = tz or cls.UTC
        return int(datetime.now(tz=tz).timestamp())
    def iso(cls, tz: ZoneInfo = None) -> str:
        tz = tz or cls.UTC
        return datetime.now(tz=tz).isoformat()
    def log(cls, tz: ZoneInfo = None) -> str:
        tz = tz or cls.UTC
        return datetime.now(tz=tz).strftime("%Y-%m-%d %H:%M:%S %Z")
