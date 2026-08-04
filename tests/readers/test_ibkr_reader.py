import pytest
from convertor.readers.ibkr_reader import IbkrReader
from convertor.currency import Currency


def make_ibkr_csv(tmp_path, content: str):
    csv_file = tmp_path / "test_ibkr.csv"
    csv_file.write_text(content)
    return csv_file


MINIMAL_HEADER = (
    "Statement,Header,Field Name,Field Value\n"
    "Statement,Data,BrokerName,Interactive Brokers Ireland Limited\n"
    "Statement,Data,Base Currency,CZK\n"
)

TRADES_HEADER = "Trades,Header,DataDiscriminator,Asset Category,Currency,Symbol,Date/Time,Quantity,T. Price,C. Price,Proceeds,Comm/Fee,Basis,Realized P/L,MTM P/L,Code\n"

DIVIDENDS_HEADER = "Dividends,Header,Currency,Date,Description,Amount\n"


@pytest.fixture
def mock_csv(tmp_path):
    content = (
        MINIMAL_HEADER
        + "Change in NAV,Header,Field Name,Field Value\n"
        + "Change in NAV,Data,Deposits & Withdrawals,5000.00\n"
        + TRADES_HEADER
        + 'Trades,Data,Order,Stocks,USD,AAPL,"2025-03-05, 11:46:04",2,204.3,208.36,-408.6,-0.35,408.95,0,8.12,O\n'
        + 'Trades,Data,Order,Stocks,USD,TSLA,"2025-03-10, 14:00:00",-1,220.0,218.0,220.0,-0.25,-204.3,15.7,-2.0,C\n'
        + DIVIDENDS_HEADER
        + "Dividends,Data,USD,2025-06-15,AAPL(US0378331005) Cash Dividend USD 0.25 per Share (Ordinary Dividend),25.0\n"
        + "Dividends,Data,Total,,,25.0\n"
    )
    return make_ibkr_csv(tmp_path, content)


def test_ibkr_reader_parses_correctly(mock_csv):
    reader = IbkrReader()
    report = reader.read(mock_csv)

    assert report.deposit == 5000.00
    assert report.deposit_currency == Currency.CZK
    assert len(report.buys) == 1
    assert len(report.sells) == 1
    assert len(report.dividends) == 1


def test_buy_transaction_details(mock_csv):
    reader = IbkrReader()
    report = reader.read(mock_csv)

    buy = report.buys[0]
    assert buy.ticker == "AAPL"
    assert buy.time == "2025-03-05 11:46:04"
    assert buy.quantity == 2.0
    assert buy.share_price == 204.3
    assert buy.total_price == 408.6
    assert buy.currency_main == Currency.USD


def test_sell_transaction_details(mock_csv):
    reader = IbkrReader()
    report = reader.read(mock_csv)

    sell = report.sells[0]
    assert sell.ticker == "TSLA"
    assert sell.time == "2025-03-10 14:00:00"
    assert sell.quantity == 1.0
    assert sell.share_price == 220.0
    assert sell.total_price == 220.0
    assert sell.currency_main == Currency.USD


def test_dividend_details(mock_csv):
    reader = IbkrReader()
    report = reader.read(mock_csv)

    div = report.dividends[0]
    assert div.ticker == "AAPL"
    assert div.time == "2025-06-15 00:00:00"
    assert div.amount == 25.0
    assert div.currency == Currency.USD


def test_options_are_skipped(tmp_path):
    content = (
        MINIMAL_HEADER
        + TRADES_HEADER
        + 'Trades,Data,Order,Stocks,USD,AAPL,"2025-03-05, 11:00:00",1,100.0,100.0,-100.0,-0.1,100.1,0,0,O\n'
        + 'Trades,Data,Order,Equity and Index Options,USD,AAPL 15JAN26 200 C,"2025-03-05, 11:00:00",1,5.0,5.1,-500.0,-0.25,500.25,0,10.0,O\n'
    )
    csv_file = make_ibkr_csv(tmp_path, content)

    report = IbkrReader().read(csv_file)

    assert len(report.buys) == 1
    assert report.buys[0].ticker == "AAPL"


def test_subtotals_and_totals_are_skipped(tmp_path):
    content = (
        MINIMAL_HEADER
        + TRADES_HEADER
        + 'Trades,Data,Order,Stocks,USD,AAPL,"2025-03-05, 11:00:00",1,100.0,100.0,-100.0,-0.1,100.1,0,0,O\n'
        + "Trades,SubTotal,,Stocks,USD,AAPL,,1,,,-100.0,-0.1,100.1,0,0,\n"
        + "Trades,Total,,Stocks,USD,,,,,,,-100.0,-0.1,0,0,0,\n"
    )
    csv_file = make_ibkr_csv(tmp_path, content)

    report = IbkrReader().read(csv_file)

    assert len(report.buys) == 1


def test_dividend_totals_are_skipped(tmp_path):
    content = (
        MINIMAL_HEADER
        + DIVIDENDS_HEADER
        + "Dividends,Data,USD,2025-06-15,AAPL(US0378331005) Cash Dividend USD 0.25 per Share,25.0\n"
        + "Dividends,Data,Total,,,25.0\n"
        + "Dividends,Data,Total in CZK,,,612.5\n"
    )
    csv_file = make_ibkr_csv(tmp_path, content)

    report = IbkrReader().read(csv_file)

    assert len(report.dividends) == 1
    assert report.dividends[0].amount == 25.0


def test_dividend_ticker_extracted_from_description(tmp_path):
    content = (
        MINIMAL_HEADER
        + DIVIDENDS_HEADER
        + "Dividends,Data,USD,2025-12-10,PYPL(US70450Y1038) Cash Dividend USD 0.14 per Share (Ordinary Dividend),14.0\n"
    )
    csv_file = make_ibkr_csv(tmp_path, content)

    report = IbkrReader().read(csv_file)

    assert report.dividends[0].ticker == "PYPL"


def test_currency_extracted_from_statement(tmp_path):
    content = (
        "Statement,Header,Field Name,Field Value\n"
        "Statement,Data,Base Currency,USD\n"
        + TRADES_HEADER
    )
    csv_file = make_ibkr_csv(tmp_path, content)

    report = IbkrReader().read(csv_file)

    assert report.deposit_currency == Currency.USD


def test_multiple_deposits_summed(tmp_path):
    content = (
        MINIMAL_HEADER
        + "Change in NAV,Data,Deposits & Withdrawals,3000.00\n"
        + "Change in NAV,Data,Deposits & Withdrawals,2000.00\n"
    )
    csv_file = make_ibkr_csv(tmp_path, content)

    report = IbkrReader().read(csv_file)

    assert report.deposit == 5000.00


def test_multiple_currencies(tmp_path):
    content = (
        MINIMAL_HEADER
        + TRADES_HEADER
        + 'Trades,Data,Order,Stocks,USD,AMZN,"2025-04-01, 10:00:00",3,180.0,181.0,-540.0,-0.3,540.3,0,3.0,O\n'
        + 'Trades,Data,Order,Stocks,EUR,TUI1d,"2025-04-02, 09:00:00",100,7.4,7.3,-740.0,-1.3,741.3,0,-10.0,O\n'
    )
    csv_file = make_ibkr_csv(tmp_path, content)

    report = IbkrReader().read(csv_file)

    assert len(report.buys) == 2
    assert report.buys[0].currency_main == Currency.USD
    assert report.buys[1].currency_main == Currency.EUR


def test_empty_csv(tmp_path):
    content = MINIMAL_HEADER
    csv_file = make_ibkr_csv(tmp_path, content)

    report = IbkrReader().read(csv_file)

    assert len(report.buys) == 0
    assert len(report.sells) == 0
    assert len(report.dividends) == 0
    assert report.deposit == 0.0
