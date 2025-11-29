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
