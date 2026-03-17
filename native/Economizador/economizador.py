from adapters.Redis.MainClass import RedisClient
from typing import Dict, Optional
from dataclasses import dataclass, field
#así sea postgresql, mysql, mariadb, presentan el mismo frontend
from adapters.Postgresql.MainClass import PostgresClient as SqlClient, Select
from native.Library.others import DatabaseSchema, b64_encrypt, b64_decrypt
import json

@dataclass(frozen=True)
class Session:
    _user: Optional[str] = field(default="python")
    _escena: Optional[str] = field(default="main")
    password: Optional[str] = field(default="123abc")
    address: Optional[str] = field(default=None)
    def __post_init__(self):
        if self.address is None and self._user and self._escena and self.password:
            object.__setattr__(
                self,
                "address",
                b64_encrypt(
                    text=f"{self._user}@{self._escena}",
                    key=self.password
                )
            )
    @property
    def user(self):
        if self._user is not None:
            return self._user
        if self.address and self.password:
            try:
                decrypted = b64_decrypt(self.address, key=self.password)
                return decrypted.split("@", 1)[0]
            except Exception:
                return None
        return None
    @property
    def escena(self):
        if self._escena is not None:
            return self._escena
        if self.address and self.password:
            try:
                decrypted = b64_decrypt(self.address, key=self.password)
                return decrypted.split("@", 1)[1]
            except Exception:
                return None
        return None
    def __iter__(self):
        for key in ["user", "escena", "password", "address"]:
            yield (key, getattr(self, key))

class Economizador:
    def __init__(
        self,
        redis_server: RedisClient,
        sql_server: SqlClient,
        session: Optional[Session] = None,
        ttl: Optional[int] = 1440
    ):
        self.redis_server = redis_server
        self.sql_server = sql_server
        self.known_schemas: Dict[str, DatabaseSchema] = {}
        self.session = session
        self.ttl = ttl
    def register_schema(self, schema_name: str = "public"):
        schema = self.sql_server.extract_schema(schema_name)
        if schema.id in self.known_schemas:
            raise ValueError(f"Schema '{schema.id}' ya registrado")
        self.known_schemas[schema.id] = schema
    def refresh_schema(self, schema_name="public"):
        schema = self.sql_server.extract_schema(schema_name)
        self.known_schemas[schema.id] = schema
    def select(
        self,
        built_query: Select,
        session: Optional[Session] = None,
    ):
        s = session if session else self.session
        sql, params = built_query.build()
        cache_key = f"{s.address}:{hash(sql)}:{params}"
        cached = self.redis_server.get(cache_key)
        if cached:
            return json.loads(cached)
        result = self.sql_server.query(sql=sql, params=params, fetch=True)
        columns_requested = built_query.get_columns()
        records = [dict(zip(columns_requested, row)) for row in result]
        self.redis_server.set(cache_key, json.dumps(records), ex=self.ttl)
        return records