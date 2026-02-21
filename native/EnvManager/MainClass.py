#Componentes a usar
from dotenv import load_dotenv, dotenv_values #type:ignore
from native.EnvManager.Errors import *
from pathlib import Path
import os, importlib, sys

root_str_path = "this_path"
root_path = Path(root_str_path)

class EnvManager:
    def __init__(
        self
    ):
        pass
    def metainf(self):
        meta = {}
        for k, v in self.__dict__.items():
            meta[k] = v
        return meta
    def load_vars_from_env(
        self, 
        path:Path=None,
        inject:bool=False
    ):
        env = {}
        if not os.path.exists(path):
            raise EnvManagerError(f"Env path no existe")
        env_vars = dotenv_values(path)
        if inject:
            load_dotenv(dotenv_path=path, override=True)
        for k, v in env_vars.items():
            env[k] = v
        return env
    def path_to_pypath(
        self,
        path:str, 
        package_root:str
    ):
        path = Path(path).resolve()
        package_root = Path(package_root).resolve()
        if not path.is_file():
            raise EnvManagerError(f"No es un archivo válido: {path}")
        if path.suffix != ".py":
            raise EnvManagerError(f"No es un archivo Python: {path}")
        try:
            relative = path.relative_to(package_root)
        except ValueError:
            raise EnvManagerError("El archivo no está dentro del package_root")
        return ".".join(relative.with_suffix("").parts)
    def for_in_directory(
        self,
        directory: Path,
        ignored_dirs: list = []
    ):
        content = {}
        for item in directory.iterdir():
            name = item.name
            if item.is_dir():
                if name in ignored_dirs:
                    pass
                else:
                    content[name] = {}
                    content[name]["type"] = "dir"
                    content[name]["source"] = item.as_posix()
            elif item.is_file():
                if item.suffix.replace('.', '') == "py":
                    if name in ["vm.py", "main.py", "__init__.py"]:
                        pass
                    else:
                        content[name] = {}
                        content[name]["type"] = "module"
                        content[name]["source"] = item.as_posix()
                        content[name]["pypath"] = self.path_to_pypath(item.as_posix(), root_path)
        return content

    """def mapApplications(
        self, 
        app, 
        *,
        logmanager, 
        authmanager, 
        mntmicroapp
    ):
        microapps = self.for_in_directory(root_path / "microapps")
        for _, v in microapps.items():
            kind, source = v["type"], v["source"]
            if kind != "dir":
                continue
            template = self.for_in_directory(Path(source))
            for filename, meta in template.items():
                if filename != "Endpoints.py":
                    continue
                pypath = meta["pypath"]
                url_prefix = pypath.split(".")[1]
                self._mapApplication(
                    app=app,
                    pypath=pypath,
                    url_prefix=url_prefix,
                    logmanager=logmanager,
                    authmanager=authmanager,
                    mntmicroapp=mntmicroapp
                )"""
    
    def mapApplications(
        self, 
        app, 
        *,
        logmanager, 
        authmanager, 
        mntmicroapp
    ):
        microapps = self.for_in_directory(root_path / "microapps")
        for _, v in microapps.items():
            if v["type"] != "dir":
                continue
            source = Path(v["source"])
            endpoints_path = source / "web" / "Endpoints.py"
            if not endpoints_path.exists():
                continue
            pypath = self._path_to_module(endpoints_path)
            url_prefix = pypath.split(".")[1]
            self._mapApplication(
                app=app,
                pypath=pypath,
                url_prefix=url_prefix,
                logmanager=logmanager,
                authmanager=authmanager,
                mntmicroapp=mntmicroapp
            )
            
    def _mapApplication(
        self, 
        *, 
        app, 
        pypath: str, 
        url_prefix: str, 
        logmanager, 
        authmanager, 
        mntmicroapp
    ):
        if not app:
            raise EnvManagerError("La aplicación Flask es inválida.")
        if not pypath:
            raise EnvManagerError("El pypath es inválido.")
        try:
            module = importlib.import_module(pypath)
        except Exception as e:
            raise EnvManagerError(f"Error importando '{pypath}': {e}")
        if not hasattr(module, "register"):
            raise EnvManagerError(
                f"El módulo '{pypath}' debe exponer una función register(app, logger)."
            )
        module.register(
            app=app, 
            logmanager=logmanager,
            authmanager=authmanager, 
            mntmicroapp=mntmicroapp
        )
        print(f"Registrado: /{url_prefix} ← {pypath}")
