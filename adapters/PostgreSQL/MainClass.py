from native.EnvManager.MainClass import *
from adapters.PostgreSQL.Errors import *

import psycopg2, os #type:ignore
from psycopg2 import pool #type:ignore
from pathlib import Path
from contextlib import contextmanager

class PostgresClient:
    def __init__(
        self, 
        host:str, 
        port:int,
        user:str,
        password:str
    ):
        self.my_relative_path = Path(__file__).resolve().parent.relative_to(root_path)
        self.my_full_path = root_str_path / self.my_relative_path
        self.env = EnvManager().load_vars_from_env(self.my_full_path / ".env")
        self.db = psycopg2.pool.ThreadedConnectionPool(
            1, 
            10,
            dbname=str(
                self.env.get("database")
            ),
            user=user,
            password=password,
            host=host,
            port=port
        )
    
    def metainf(self):
        meta = {}
        for k, v in self.__dict__.items():
            meta[k] = v
        return meta
    
    @contextmanager
    def get_conn(self):
        conn = self.db.getconn()
        try:
            yield conn
        finally:
            self.db.putconn(conn)
    
    def query(
        self, 
        sql, 
        params=None, 
        fetch=False
    ):
        params = params or ()
        with self.get_conn() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    if fetch:
                        result = cur.fetchall()
                    else:
                        result = None
                    conn.commit()
                    return result
            except Exception as e:
                conn.rollback()
                raise PostgresClientError(e)

    def _fetch_one_value(self, query: str, params: tuple):
        result = self.query(
            query,
            params,
            fetch=True,
        )
        return result[0][0] if result else None