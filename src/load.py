from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

CSV = Path("data") / "products_clean.csv"
DB = Path("data") / "fake_store.db"

def load_to_sqlite(csv_path=CSV, db_path=DB, table_name="products"):
    if not csv_path.exists():
        raise SystemExit(f"No existe {csv_path}. Ejecutá extract + transform primero.")
    df = pd.read_csv(csv_path)
    engine = create_engine(f"sqlite:///{db_path}")
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    print(f"Cargado en: {db_path} (tabla: {table_name})")

if __name__ == "__main__":
    load_to_sqlite()
