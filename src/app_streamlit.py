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


# -------------------------
# Aplicar filtros al DataFrame
# -------------------------
min_sel, max_sel = price_range  # price_range viene del slider

# 1) filtro por categoría
if selected_categories:
    cond_cat = df['category_name'].isin(selected_categories)
else:
    cond_cat = pd.Series([True] * len(df), index=df.index)

# 2) filtro por rango de precio
cond_price = df['price'].between(min_sel, max_sel)

# 3) filtro por búsqueda de texto (partial match, case-insensitive)
if search_text and search_text.strip() != "":
    cond_text = df['title'].str.contains(search_text, case=False, na=False)
else:
    cond_text = pd.Series([True] * len(df), index=df.index)

# 4) combinar condiciones
filtered_df = df[ cond_cat & cond_price & cond_text ].copy()

# -------------------------
# Mostrar KPIs y tabla simple
# -------------------------
st.header("Visión general filtrada")
col1, col2 = st.columns(2)
col1.metric("Productos (filtrados)", len(filtered_df))
col2.metric("Precio promedio", f"${filtered_df['price'].mean():.2f}" if len(filtered_df) else "—")

st.subheader("Resultados (primera vista)")
st.dataframe(filtered_df.reset_index(drop=True).head(50))

