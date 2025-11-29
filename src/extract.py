from pathlib import Path
import pandas as pd
from src.utils import safe_get

BASE = "https://api.escuelajs.co/api/v1"
OUT = Path("data") / "products_raw.csv"

def extract_products(batch_size=100):
    all_products = []
    offset = 0
    while True:
        params = {"limit": batch_size, "offset": offset}
        batch = safe_get(f"{BASE}/products", params=params)
        if not batch:
            break
        all_products.extend(batch)
        offset += len(batch)
        if len(batch) < batch_size:
            break
    return pd.json_normalize(all_products)

if __name__ == "__main__":
    Path("data").mkdir(parents=True, exist_ok=True)
    df = extract_products()
    df.to_csv(OUT, index=False, encoding="utf-8")
    print(f"Productos extraídos: {len(df)} -> {OUT}")
