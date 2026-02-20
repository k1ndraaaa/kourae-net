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
        self.my_relative_path = Path(__file__).resolve().parent.relative_to(root_path)
        self.my_full_path = root_str_path / self.my_relative_path
        # Env
        self.env = EnvManager().load_vars_from_env(self.my_full_path / ".env")
        self.client = Minio(
            f"{host}:{port}",
            access_key=user,
            secret_key=password,
            secure=False  # local, sin SSL
        )
    
    def metainf(self):
        meta = {}
        for k, v in self.__dict__.items():
            meta[k] = v
        return meta
    
    def healthcheck(self):
        try:
            self.client.list_buckets()
            return True
        except Exception as e:
            raise MinioError(f"MinIO no responde: {e}")
    
    def ensure_bucket(self, bucket: str):
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)
    