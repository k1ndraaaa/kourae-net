from typing import BinaryIO, Protocol, Dict
from dataclasses import dataclass, field
import hashlib, json, base64

def human_readable_size(size_bytes: int):
    if size_bytes == 0:
        return "0B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(units)-1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f}{units[i]}"

def b64_encrypt(text: str, key: str) -> str:
    text_bytes = text.encode()
    key_bytes = key.encode()
    encrypted_bytes = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(text_bytes)])
    return base64.urlsafe_b64encode(encrypted_bytes).decode()

def b64_decrypt(token: str, key: str) -> str:
    encrypted_bytes = base64.urlsafe_b64decode(token.encode())
    key_bytes = key.encode()
    decrypted_bytes = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(encrypted_bytes)])
    return decrypted_bytes.decode()

class Row:
    ...

class UserForm(Protocol):
    #id lo produce db, así que ni lo pongo
    username: str
    password: str | bytes

class UserUpdateForm(Protocol):
    user_id: int
    username: str | None
    password: str | bytes | None

class FileForm(Protocol):
    user_id: int #inmutable

    filename: str 
    ext: str #inmutable
    
    mime_type: str #inmutable
    size: int #inmutable
    
    bucket: str #inmutable
    object_key: str #inmutable

class FileUpdateForm(Protocol):
    user_id: int #Sólo se pasa como referencia al archivo guardado
    filename: str

@dataclass(frozen=True)
class StorageObject:
    bucket: str
    object_key: str
    data: BinaryIO
    length: int
    mime_type: str

@dataclass(frozen=True)
class StoragePointer:
    bucket: str
    object_key: str

class SqlClient:
    pass

@dataclass
class ColumnSchema:
    name: str
    type: str
    nullable: bool

@dataclass
class TableSchema:
    name: str
    columns: Dict[str, str]

@dataclass
class DatabaseSchema:
    id: str
    tables: Dict[str, TableSchema] = field(default_factory=dict)
    version: str = ""
    def compute_version(self):
        structure = {
            table_name: table.columns
            for table_name, table in sorted(self.tables.items())
        }
        serialized = json.dumps(structure, sort_keys=True)
        self.version = hashlib.sha256(serialized.encode()).hexdigest()