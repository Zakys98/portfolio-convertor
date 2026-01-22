from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path

from convertor.stocks.stock import Stock


class Reader(ABC):

    @abstractmethod
    def read(self, input_file: Path) -> tuple[Sequence[Stock], Sequence[Stock], float]:
        pass
