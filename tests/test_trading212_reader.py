import pytest
from convertor.readers.trading212_reader import Trading212Reader


@pytest.fixture
def mock_csv(tmp_path):
    """Creates a temporary CSV file for testing."""
    csv_file = tmp_path / "test_t212.csv"
    content = (
        "Action,Ticker,Time,Total\n"
        "Deposit,,2023-01-01 10:00:00,1000.00\n"
        "Market buy,AAPL,2023-01-02 15:00:00,150.00\n"
        "Market sell,TSLA,2023-01-03 16:00:00,200.00\n"
        "Dividend (Dividend),MSFT,2023-01-04 09:00:00,5.50\n"
    )
    csv_file.write_text(content)
    return csv_file


def test_trading212_reader_parses_correctly(mock_csv):
    reader = Trading212Reader()

    report = reader.read(mock_csv)

    assert report.deposit == 1000.00
    assert len(report.buys) == 1
    assert report.buys[0].ticker == "AAPL"
    assert report.buys[0].time == "2023-01-02 15:00:00"

    assert len(report.sells) == 1
    assert report.sells[0].ticker == "TSLA"
    assert report.sells[0].time == "2023-01-03 16:00:00"

    assert len(report.dividends) == 1
    assert report.dividends[0].ticker == "MSFT"
    assert report.dividends[0].amount == 5.50
    assert report.dividends[0].time == "2023-01-04 09:00:00"


def test_empty_csv(tmp_path):
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("Action,Ticker,Time,Total\n")

    reader = Trading212Reader()
    report = reader.read(csv_file)

    assert report.deposit == 0
    assert len(report.buys) == 0


def test_aggregation_logic(tmp_path):
    csv_file = tmp_path / "multi_test.csv"
    content = (
        "Action,Ticker,Time,Total\n"
        "Deposit,,2023-01-01,500.00\n"
        "Deposit,,2023-01-02,250.00\n"
        "Market buy,AAPL,2023-01-02,100.00\n"
        "Limit buy,AAPL,2023-01-03,100.00\n"
    )
    csv_file.write_text(content)

    reader = Trading212Reader()
    report = reader.read(csv_file)

    assert report.deposit == 750.00
    assert len(report.buys) == 2


def test_unknown_action_graceful_skip(tmp_path):
    csv_file = tmp_path / "unknown.csv"
    content = (
        "Action,Ticker,Time,Total\n"
        "Interest on cash,,2023-01-01,1.50\n"
        "Market buy,AAPL,2023-01-02,100.00\n"
    )
    csv_file.write_text(content)

    reader = Trading212Reader()
    report = reader.read(csv_file)

    assert len(report.buys) == 1
    assert report.deposit == 0


def test_missing_action_column(tmp_path):
    csv_file = tmp_path / "missing.csv"
    content = "Action,Ticker,Time,Total\n" ",AAPL,2023-01-02,100.00\n"
    csv_file.write_text(content)

    reader = Trading212Reader()
    report = reader.read(csv_file)

    assert len(report.buys) == 0
    assert len(report.sells) == 0
