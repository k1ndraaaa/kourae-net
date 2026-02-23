from native.EnvManager.MainClass import *
from adapters.Redis.Errors import *

import redis #type:ignore
from contextlib import contextmanager


class RedisClient:
    def __init__(
        self,
        host: str,
        port: int,
        db: int
    ):
        try:
            self.my_relative_path = Path(__file__).resolve().parent.relative_to(root_path)
            self.my_full_path = root_str_path / self.my_relative_path
            self.env = EnvManager().load_vars_from_env(self.my_full_path / ".env")
        except Exception as e:
            raise ClassConstructionError(e) from e

        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True
            )
        except Exception as e:
            raise AdapterError(e) from e
        
    def healthcheck(self) -> bool:
        try:
            return self.client.ping()
        except Exception as e:
            raise AdapterError("Redis no responde") from e

    def set(self, key: str, value: str, ex: int | None = None):
        try:
            self.client.set(name=key, value=value, ex=ex)
        except Exception as e:
            raise RedisClientError(e) from e

    def get(self, key: str):
        try:
            return self.client.get(name=key)
        except Exception as e:
            raise RedisClientError(e) from e

    def delete(self, key: str):
        try:
            self.client.delete(key)
        except Exception as e:
            raise RedisClientError(e) from e