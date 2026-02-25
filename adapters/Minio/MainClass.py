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