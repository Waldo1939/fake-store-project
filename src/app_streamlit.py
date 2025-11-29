import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path

DB = Path("data") / "fake_store.db"

@st.cache_data
def load_data():
    engine = create_engine(f"sqlite:///{DB}")
    return pd.read_sql("select * from products", engine)

st.title("Fake Store — Product Insights")

if not DB.exists():
    st.warning("No se encontró la DB. Corre primero: python -m src.extract ; python -m src.transform ; python -m src.load")
else:
    df = load_data()
    st.metric("Productos", len(df))
    st.write(df.head())
    st.subheader("Precio promedio por categoría")
    st.bar_chart(df.groupby("category_name")["price"].mean())


# -------------------------
# Sidebar filters (primer paso)
# -------------------------

st.sidebar.title("Filtros")

# 1) Categoría (multiselect)
all_categories = sorted(df['category_name'].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect("Categoría", options=all_categories, default=all_categories)

# 2) Rango de precios (slider)
min_price = float(df['price'].min())
max_price = float(df['price'].max())
price_range = st.sidebar.slider("Rango de precio", min_value=min_price, max_value=max_price, value=(min_price, max_price))

# 3) Buscador por texto (input)
search_text = st.sidebar.text_input("Buscar producto (por título)")
