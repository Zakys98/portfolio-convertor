import csv
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Calculate average price and amount for each position.")
    parser.add_argument("input_csv", type=Path, help="Path to the converted portfolio CSV file")
    parser.add_argument("-o", "--output", type=Path, default=Path("positions_summary.csv"), help="Output summary CSV file")
    args = parser.parse_args()

    if not args.input_csv.exists():
        print(f"Error: Input file {args.input_csv} does not exist.")
        return

    positions = {}

    with args.input_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row.get("ticker")
            tx_type = row.get("type")
            
            if not ticker or tx_type not in ("BUY", "SELL"):
                continue
                
            qty_str = row.get("quantity", "0")
            price_str = row.get("price", "0")
            currency = row.get("currency", "")
            
            try:
                qty = float(qty_str) if qty_str else 0.0
                price = float(price_str) if price_str else 0.0
            except ValueError:
                continue
                
            if ticker not in positions:
                positions[ticker] = {"quantity": 0.0, "total_cost": 0.0, "currency": currency}
                
            pos = positions[ticker]
            
            if tx_type == "BUY":
                pos["quantity"] += qty
                pos["total_cost"] += qty * price
            elif tx_type == "SELL":
                # Selling reduces the total quantity but keeps the average cost per share the same
                if pos["quantity"] > 0:
                    avg_price = pos["total_cost"] / pos["quantity"]
                    pos["quantity"] -= qty
                    # Handle floating point precision issues for fully closed positions
                    if pos["quantity"] <= 1e-8:
                        pos["quantity"] = 0.0
                        pos["total_cost"] = 0.0
                    else:
                        pos["total_cost"] -= qty * avg_price

    # Prepare output data
    results = []
    for ticker, data in positions.items():
        qty = data["quantity"]
        # Skip fully closed positions, or include them with 0 quantity?
        # Including all of them with >0 quantity gives a snapshot of current holdings.
        if qty > 0:
            avg_price = data["total_cost"] / qty
            results.append({
                "ticker": ticker,
                "quantity": round(qty, 6),
                "average_price": round(avg_price, 4),
                "currency": data["currency"]
            })
        
    # Sort alphabetically by ticker
    results.sort(key=lambda x: x["ticker"])

    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ticker", "quantity", "average_price", "currency"])
        writer.writeheader()
        writer.writerows(results)

    print(f"Summary successfully written to {args.output.absolute()}")

if __name__ == "__main__":
    main()
