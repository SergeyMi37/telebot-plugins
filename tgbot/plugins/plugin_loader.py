# plugins/plugin_loader.py   Загрузчик модулей
import importlib, pkgutil
from pathlib import Path
from tgbot.plugins.base_plugin import BasePlugin

def discover_plugins(plugins_dir="plugins"):
    plugins = {}
    plugins_path = Path(__file__).parent #/ plugins_dir
    for finder, name, _ in pkgutil.iter_modules([str(plugins_path)]):
        if name.endswith("_plugin"):
            module = importlib.import_module(f"tgbot.plugins.{name}")
            for item in dir(module):
                obj = getattr(module, item)
                if isinstance(obj, type) and issubclass(obj, BasePlugin) and obj != BasePlugin:
                    plugins[name] = obj()
    return plugins