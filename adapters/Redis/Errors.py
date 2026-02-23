from native.EnvManager.Errors import *

class _RedisBaseError(BaseError): pass
class RedisClientError(_RedisBaseError): pass