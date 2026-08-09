from abc import ABC, abstractmethod
from pathlib import Path


class Reader[TReport](ABC):

    @abstractmethod
    def read(self, input_file: Path) -> TReport:
        pass
