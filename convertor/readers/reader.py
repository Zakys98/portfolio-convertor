from abc import ABC, abstractmethod


class Reader[T](ABC):

    def __init__(self) -> None:
        super().__init__()
        self._buys: list[T] = []
        self._sells: list[T] = []
        self._deposits: float = 0.0

    @property
    def buys(self) -> list[T]:
        return self._buys

    @property
    def sells(self) -> list[T]:
        return self._sells

    @property
    def deposits(self) -> float:
        return self._deposits

    @abstractmethod
    def read(self, input_file: str) -> None:
        pass

    @abstractmethod
    def dump_buys_to_json(self) -> list[dict[str, str | float]]:
        pass

    @abstractmethod
    def dump_sells_to_json(self) -> list[dict[str, str | float]]:
        pass
