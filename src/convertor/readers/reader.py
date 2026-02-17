from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

TReport = TypeVar("TReport")


class Reader(ABC, Generic[TReport]):

    @abstractmethod
    def read(self, input_file: Path) -> TReport:
        pass
