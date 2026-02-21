from native.EnvManager.MainClass import *

class WebResponse:
    def __init__(self, status: int = 200, data=None):
        self.status = status
        self.data = data
        self.error = None
        self.meta = {}
        """self.my_relative_path = Path(__file__).resolve().parent.relative_to(root_path)
        self.my_full_path = Path(root_str_path / self.my_relative_path)
        self.env = EnvManager().load_vars_from_env(
            Path(self.my_full_path / ".env")
        )"""
    def metainf(self):
        meta = {}
        for k, v in self.__dict__.items():
            meta[k] = v
        return meta
    @property
    def ok(self) -> bool:
        return self.status < 400
    def set_status(self, status: int):
        self.status = status
        return self
    def success(self, data=None, status: int = 200):
        self.status = status
        self.data = data
        self.error = None
        return self
    def fail(
        self,
        message: str,
        status: int = 400,
        *,
        code: str | None = None,
        details=None
    ):
        self.status = status
        self.data = None
        self.error = {
            "message": message,
            "code": code,
            "details": details
        }
        return self
    def add_meta(self, key: str, value):
        self.meta[key] = value
        return self
    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "status": self.status,
            "data": self.data,
            "error": self.error,
            "meta": self.meta
        }