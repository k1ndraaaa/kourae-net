from adapters.Redis.MainClass import RedisClient
from typing import Dict, Optional
#así sea postgresql, mysql, mariadb, en un futuro presentarían el mismo frontend
from adapters.Postgresql.MainClass import PostgresClient as SqlClient, Select, Update, Delete
from native.Library.commons import DatabaseSchema, Session
import json

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
        for row in records:
            row_id = row.get("id")
            if row_id is None:
                continue
            row_hash = hash(json.dumps(row, sort_keys=True))
            self.redis_server.hset(f"table:{built_query.table}", row_id, row_hash)
            self.redis_server.sadd(f"row:{row_id}:{built_query.table}", cache_key)
        self.redis_server.set(cache_key, json.dumps(records), ex=self.ttl)
        return records
    def update(self, built_query: Update, session: Optional[Session] = None):
        s = session if session else self.session
        sql, params = built_query.build()
        self.sql_server.query(sql, params)
        table_name = built_query.table
        where_conditions = built_query._where
        if not where_conditions:
            return
        select_query = Select(table_name)
        for column, operator, value in where_conditions:
            select_query.where(column, operator, value)
        affected_rows = self.sql_server.query(*select_query.build(), fetch=True)
        columns = [col[0] for col in self.sql_server.query(
            "SELECT column_name FROM information_schema.columns WHERE table_name=%s",
            (table_name,), fetch=True
        )]
        records = [dict(zip(columns, row)) for row in affected_rows]
        for row in records:
            row_id = row.get("id")
            if row_id is None:
                continue
            new_hash = hash(json.dumps(row, sort_keys=True))
            old_hash = self.redis_server.hget(f"table:{table_name}", row_id)
            if new_hash != old_hash:
                self.redis_server.hset(f"table:{table_name}", row_id, new_hash)
                for cache_key in self.redis_server.smembers(f"row:{row_id}:{table_name}") or []:
                    self.redis_server.delete(cache_key)
    def delete(self, built_query: Delete, session: Optional[Session] = None):
        s = session if session else self.session
        table_name = built_query.table
        where_conditions = built_query._where
        if not where_conditions:
            return
        select_query = Select(table_name)
        for column, operator, value in where_conditions:
            select_query.where(column, operator, value)
        affected_rows = self.sql_server.query(*select_query.build(), fetch=True)
        columns = [col[0] for col in self.sql_server.query(
            "SELECT column_name FROM information_schema.columns WHERE table_name=%s",
            (table_name,), fetch=True
        )]
        records = [dict(zip(columns, row)) for row in affected_rows]
        for row in records:
            row_id = row.get("id")
            if row_id is None:
                continue
            self.redis_server.hdel(f"table:{table_name}", row_id)
            for cache_key in self.redis_server.smembers(f"row:{row_id}:{table_name}") or []:
                self.redis_server.delete(cache_key)
            self.redis_server.delete(f"row:{row_id}:{table_name}")
        sql, params = built_query.build()
        self.sql_server.query(sql, params)
        