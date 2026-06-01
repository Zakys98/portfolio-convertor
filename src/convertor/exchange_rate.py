import urllib.request
from datetime import datetime, timedelta

class CNBRateFetcher:
    _cache = {}
    _year_loaded = set()

    @classmethod
    def get_eur_to_usd(cls, date_str: str) -> float:
        """
        Fetch the EUR to USD exchange rate for a given date using CNB daily rates.
        """
        if "T" in date_str:
            date_str = date_str.split("T")[0]
        
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            # fallback if it's already another format, assume today or return 1.1 roughly
            return 1.1
            
        original_year = dt.year
        
        if original_year not in cls._year_loaded:
            cls._load_year(original_year)
            
        cnb_date = dt.strftime("%d.%m.%Y")
        
        # Rewind day by day if there is no rate (weekends, holidays)
        max_lookback = 10
        lookback = 0
        while cnb_date not in cls._cache and lookback < max_lookback:
            dt = dt - timedelta(days=1)
            if dt.year != original_year and dt.year not in cls._year_loaded:
                cls._load_year(dt.year)
                original_year = dt.year
            cnb_date = dt.strftime("%d.%m.%Y")
            lookback += 1
            
        if cnb_date in cls._cache:
            rates = cls._cache[cnb_date]
            return rates['EUR'] / rates['USD']
            
        # Fallback if no rate found
        return 1.1

    @classmethod
    def _load_year(cls, year: int):
        url = f"https://www.cnb.cz/en/financial-markets/foreign-exchange-market/central-bank-exchange-rate-fixing/central-bank-exchange-rate-fixing/year.txt?year={year}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                lines = response.read().decode('utf-8').splitlines()
        except Exception as e:
            print(f"Warning: Could not fetch CNB rates for {year}: {e}")
            cls._year_loaded.add(year)
            return
            
        if not lines:
            cls._year_loaded.add(year)
            return
            
        header = lines[0].split('|')
        try:
            eur_idx = header.index('1 EUR')
            usd_idx = header.index('1 USD')
        except ValueError:
            cls._year_loaded.add(year)
            return
            
        for line in lines[1:]:
            parts = line.split('|')
            if len(parts) > max(eur_idx, usd_idx):
                date = parts[0]
                try:
                    eur = float(parts[eur_idx])
                    usd = float(parts[usd_idx])
                    cls._cache[date] = {'EUR': eur, 'USD': usd}
                except ValueError:
                    continue
                
        cls._year_loaded.add(year)
