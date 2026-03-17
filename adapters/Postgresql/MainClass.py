from native.EnvLoader.MainClass import *
from native.Library.commons import SqlClient, TableSchema, DatabaseSchema
from adapters.Postgresql.Errors import *
import psycopg2 #type:ignore
from psycopg2 import pool #type:ignore
from contextlib import contextmanager

def build_conditions(conditions):
    sql_parts = []
    params = []
    for column, operator, value in conditions:
        sql_parts.append(f"{column} {operator} %s")
        params.append(value)
    return " AND ".join(sql_parts), params
def build_set(data):
    parts = []
    params = []
    for key, value in data.items():
        parts.append(f"{key} = %s")
        params.append(value)
    return ", ".join(parts), params
class Query:
    def __init__(self, table):
        self.table = table
        self._params = []
    def params(self):
        return tuple(self._params)
    def build(self):
        raise NotImplementedError
class Select(Query):
    def __init__(self, table):
        super().__init__(table)
        self._columns = ["*"]
        self._joins = []
        self._where = []
        self._group = []
        self._having = []
        self._order = []
        self._limit = None
        self._offset = None
    def columns(self, *cols):
        self._columns = cols
        return self
    def join(self, table, condition, kind="INNER"):
        self._joins.append((kind, table, condition))
        return self
    def where(self, column, operator, value):
        self._where.append((column, operator, value))
        return self
    def group_by(self, *cols):
        self._group.extend(cols)
        return self
    def having(self, column, operator, value):
        self._having.append((column, operator, value))
        return self
    def order_by(self, *cols):
        self._order.extend(cols)
        return self
    def limit(self, n):
        self._limit = n
        return self
    def offset(self, n):
        self._offset = n
        return self
    def build(self):
        sql = f"SELECT {', '.join(self._columns)} FROM {self.table}"
        for kind, table, cond in self._joins:
            sql += f" {kind} JOIN {table} ON {cond}"
        if self._where:
            where_sql, params = build_conditions(self._where)
            sql += f" WHERE {where_sql}"
            self._params.extend(params)
        if self._group:
            sql += " GROUP BY " + ", ".join(self._group)
        if self._having:
            having_sql, params = build_conditions(self._having)
            sql += f" HAVING {having_sql}"
            self._params.extend(params)
        if self._order:
            sql += " ORDER BY " + ", ".join(self._order)
        if self._limit is not None:
            sql += f" LIMIT {self._limit}"
        if self._offset is not None:
            sql += f" OFFSET {self._offset}"
        return sql, self.params()
    def get_columns(self):
        return self._columns
class Insert(Query):
    def __init__(self, table):
        super().__init__(table)
        self._data = {}
    def values(self, **kwargs):
        self._data.update(kwargs)
        return self
    def build(self):
        columns = ", ".join(self._data.keys())
        placeholders = ", ".join(["%s"] * len(self._data))
        self._params.extend(self._data.values())
        sql = f"INSERT INTO {self.table} ({columns}) VALUES ({placeholders})"
        return sql, self.params()
class Update(Query):
    def __init__(self, table):
        super().__init__(table)
        self._data = {}
        self._where = []
    def set(self, **kwargs):
        self._data.update(kwargs)
        return self
    def where(self, column, operator, value):
        self._where.append((column, operator, value))
        return self
    def build(self):
        set_sql, set_params = build_set(self._data)
        sql = f"UPDATE {self.table} SET {set_sql}"
        self._params.extend(set_params)
        if self._where:
            where_sql, params = build_conditions(self._where)
            sql += f" WHERE {where_sql}"
            self._params.extend(params)
        return sql, self.params()
class Delete(Query):
    def __init__(self, table):
        super().__init__(table)
        self._where = []
    def where(self, column, operator, value):
        self._where.append((column, operator, value))
        return self
    def build(self):
        sql = f"DELETE FROM {self.table}"
        if self._where:
            where_sql, params = build_conditions(self._where)
            sql += f" WHERE {where_sql}"
            self._params.extend(params)
        return sql, self.params()

class PostgresClient(SqlClient):
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
    def query(self, sql_or_query, params=None, fetch=False):
        if hasattr(sql_or_query, "build"):
            sql, params = sql_or_query.build()
        else:
            sql = sql_or_query
            params = params or ()
        with self.get_conn() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    if fetch:
                        result = cur.fetchall()
                    else:
                        result = None
                    if not fetch:
                        conn.commit()
                    return result
            except Exception as e:
                conn.rollback()
                raise PostgresClientError(e) from e
    def scalar(self, query):
        result = self.query(query, fetch=True)
        return result[0][0] if result else None
    def extract_schema(self, schema_name="public") -> DatabaseSchema:
        tables = self.query(
            """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
            """,
            (schema_name,),
            fetch=True
        )
        schema = DatabaseSchema(id=schema_name)
        for (table_name,) in tables:
            columns = self.query(
                """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = %s
                    AND table_name = %s
                """,
                (schema_name, table_name),
                fetch=True
            )
            schema.tables[table_name] = TableSchema(
                name=table_name,
                columns={col: dtype for col, dtype in columns}
            )
        schema.compute_version()
        return schema