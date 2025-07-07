# plugins/base_plugin.py
from abc import ABC, abstractmethod
from telegram.ext import Dispatcher

class BasePlugin(ABC):
    @abstractmethod
    def setup_handlers(self, dp: Dispatcher):
        pass