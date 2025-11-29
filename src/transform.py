from pathlib import Path
import pandas as pd

IN = Path("data") / "products_raw.csv"
OUT = Path("data") / "products_clean.csv"

def transform_products(df):
    df = df.copy()
    fields = {
      "id": "id",
      "title": "title",
      "price": "price",
      "description": "description",
      "category.id": "category_id",
      "category.name": "category_name",
      "images": "images"
    }
    cols = [k for k in fields.keys() if k in df.columns]
    df = df[cols].rename(columns={k: fields[k] for k in cols})
    if "images" in df.columns:
        df["image_url"] = df["images"].apply(lambda x: x[0] if isinstance(x, list) and x else None)
        df = df.drop(columns=["images"])
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price"])
    return df

if __name__ == "__main__":
    if not IN.exists():
        raise SystemExit(f"No existe el archivo {IN}. Ejecutá primero: python -m src.extract")
    df_raw = pd.read_csv(IN)
    df_clean = transform_products(df_raw)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(OUT, index=False, encoding="utf-8")
    print(f"Transform complete, filas: {len(df_clean)} -> {OUT}")
