from native.EnvManager.MainClass import *
from adapters.Postgresql.Errors import *

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
        password:str,
        database: str,
        min_connections: int = 1,
        max_connections: int = 3
    ):
        try:
            self.client = psycopg2.pool.ThreadedConnectionPool(
                min_connections,
                max_connections,
                dbname=database,
                user=user,
                password=password,
                host=host,
                port=port
            )
        except Exception as e:
            raise AdapterError(e) from e
    
    def healthcheck(self) -> bool:
        try:
            with self.get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    cur.fetchone()
            return True
        except Exception as e:
            raise AdapterError(f"PostgreSQL no responde: {e}") from e
        
    @contextmanager
    def get_conn(self):
        conn = self.client.getconn()
        try:
            yield conn
        finally:
            self.client.putconn(conn)
    
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
                raise PostgresClientError(e) from e

    def _fetch_one_value(self, query: str, params: tuple):
        result = self.query(
            query,
            params,
            fetch=True,
        )
        return result[0][0] if result else None
