from native.EnvManager.MainClass import *
from adapters.Minio.Errors import *

import os
from minio import Minio  #type:ignore
from minio.error import S3Error #type:ignore

class MinioClient:
    def __init__(
        self,
        host:str,
        port:int,
        user:str,
        password:str
    ):
        try:
            self.my_relative_path = Path(__file__).resolve().parent.relative_to(root_path)
            self.my_full_path = root_str_path / self.my_relative_path
            self.env = EnvManager().load_vars_from_env(self.my_full_path / ".env")
        except Exception as e:
            raise ClassConstructionError(e) from e
        
        try:
            self.client = Minio(
                f"{host}:{port}",
                access_key=user,
                secret_key=password,
                secure=False
            )
        except Exception as e:
            raise AdapterError(e) from e
        
    def healthcheck(self):
        try:
            self.client.list_buckets()
            return True
        except Exception as e:
            raise AdapterError(e) from e
    def ensure_bucket(self, bucket: str):
        try:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
        except Exception as e:
            raise AdapterError(e) from e