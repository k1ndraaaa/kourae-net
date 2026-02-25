from typing import BinaryIO, Union
from io import BytesIO

def to_binary_io(file_obj: Union[BinaryIO, bytes]) -> BinaryIO:
    if hasattr(file_obj, "read") and callable(file_obj.read):
        return file_obj
    if isinstance(file_obj, bytes):
        return BytesIO(file_obj)
    if hasattr(file_obj, "file"):
        return file_obj.file
    if hasattr(file_obj, "stream"):
        return file_obj.stream
    raise TypeError(f"Tipo de archivo no soportado: {type(file_obj)}")

def human_readable_size(size_bytes: int):
    if size_bytes == 0:
        return "0B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(units)-1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f}{units[i]}"