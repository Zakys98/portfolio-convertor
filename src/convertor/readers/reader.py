from abc import ABC, abstractmethod
from pathlib import Path

from convertor.report import Report


class Reader(ABC):

    @abstractmethod
    def read(self, input_file: Path) -> Report:
        pass
