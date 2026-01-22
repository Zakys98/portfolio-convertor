from .stocks.stock import Stock


class Store:

    def __init__(self) -> None:
        self._buys: list[Stock] = []
        self._sells: list[Stock] = []
        self._deposits: float = 0.0

    @property
    def buys(self) -> list[Stock]:
        return self._buys

    @property
    def sells(self) -> list[Stock]:
        return self._sells

    @property
    def deposits(self) -> float:
        return self._deposits

    @deposits.setter
    def deposits(self, value) -> None:
        self._deposits = value

    def dump_buys_to_json(self) -> list[dict[str, str | float]]:
        return [stock.model_dump() for stock in self._buys]

    def dump_sells_to_json(self) -> list[dict[str, str | float]]:
        return [stock.model_dump() for stock in self._sells]
