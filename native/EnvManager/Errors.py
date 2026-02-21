class BaseError(Exception):pass

class EnvManagerError(BaseError): 
    description = "Error relacionado al entorno"
    pass