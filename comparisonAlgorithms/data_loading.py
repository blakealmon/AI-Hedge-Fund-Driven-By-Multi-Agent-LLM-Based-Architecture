import pandas as pd
from pathlib import Path
from typing import Union

def load_price_csv(path: Union[str, Path]) -> pd.DataFrame:
    """Load a OHLCV CSV (expects columns: date, open, high, low, close, volume)."""
    df = pd.read_csv(path)
    # Normalize column names
    df.columns = [c.lower() for c in df.columns]
    # Parse date
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df = df.set_index('date')
    return df
