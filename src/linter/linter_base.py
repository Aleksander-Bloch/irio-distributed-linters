from abc import ABC, abstractmethod
from typing import Tuple

CODE_SUCCESS = 0
CODE_FAILURE = 1

class LinterBase(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        pass
    
    @abstractmethod
    def lint_code(self, code) -> Tuple[int, str]:
        pass
